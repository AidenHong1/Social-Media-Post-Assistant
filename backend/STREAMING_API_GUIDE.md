# 流式响应 API 使用指南

## 概述

流式响应功能允许前端在文案生成过程中实时接收结果，而不是等待所有变体生成完成后一次性返回。这显著改善了用户体验。

## 架构设计

### 后端实现

**1. 流式生成器（`generation_service.py`）**

```python
async def create_generation_stream(
    db: Session, llm: LLMClient, req: GenerateRequest
) -> AsyncGenerator[dict, None]:
    """流式生成，逐个yield完成的变体结果"""
```

**工作流程：**
- 并发处理所有平台和变体
- 每完成一个变体立即 yield
- 使用 `as_completed()` 按完成顺序返回结果
- 所有变体完成后发送 complete 事件

**2. SSE 端点（`generate.py`）**

```python
@router.post("/generate-stream")
async def generate_stream(...):
    """使用 Server-Sent Events (SSE) 逐个返回完成的变体"""
```

**特性：**
- 使用 `StreamingResponse` 
- 媒体类型：`text/event-stream`
- 禁用缓冲确保实时传输

**3. 变体级流式生成（`orchestrator.py`）**

```python
def run_platform_variants_stream(...) -> Generator[tuple[int, PipelineResult], None, None]:
    """流式生成变体，每完成一个立即yield"""
```

### 前端实现

**1. API 客户端（`api.ts`）**

```typescript
export async function generateStream(
  req: GenerateRequest,
  onVariant: (variant: VariantOut) => void,
  onComplete: (data: {...}) => void,
  onError: (error: string) => void,
): Promise<void>
```

**工作原理：**
- 使用 `fetch` + `ReadableStream` 读取 SSE 数据
- 解析 `data: {json}\n\n` 格式
- 根据事件类型调用对应回调

**2. UI 组件（`App.tsx`）**

```typescript
await generateStream(
  req,
  (variant) => {
    // 实时显示新变体
    partialVariants.push(variant);
    setCurrentResult({...});
  },
  (data) => {
    // 所有完成后刷新历史
    refreshHistory();
  },
  (errorMsg) => {
    setError(errorMsg);
  }
);
```

## 事件格式

### 1. Variant 事件（变体完成）

```json
{
  "type": "variant",
  "data": {
    "id": 123,
    "platform": "linkedin",
    "variant_index": 0,
    "final_text": "文案内容...",
    "draft_text": "初稿内容...",
    "critique_feedback": "评审反馈...",
    "was_rewritten": true,
    "rating": null
  }
}
```

### 2. Complete 事件（全部完成）

```json
{
  "type": "complete",
  "data": {
    "request_id": 456,
    "topic": "主题",
    "brand_tone": "品牌调性",
    "created_at": "2026-07-24T12:00:00"
  }
}
```

### 3. Error 事件（错误）

```json
{
  "type": "error",
  "platform": "linkedin",
  "message": "错误信息"
}
```

## 性能对比

### 传统方式（批量返回）

```
时间线：
0s ────────────────────────── 20s
    [用户等待...] → [一次性显示所有结果]

用户感知：
- 等待 20 秒后才看到任何结果
- 体验较差
```

### 流式响应

```
时间线：
0s ─ 4s ─ 6s ─ 8s ─ 10s
    ↓    ↓    ↓    ↓
   V1   V2   V3   V4

用户感知：
- 4 秒后看到第一个结果
- 每隔 2-3 秒出现新结果
- 体验流畅
```

**关键指标：**

| 指标 | 传统方式 | 流式响应 |
|------|---------|---------|
| 首次内容时间 (TTFC) | 20秒 | **4秒** |
| 用户感知速度 | 慢 | **快** |
| 用户体验 | 焦虑等待 | **渐进呈现** |

## 使用方法

### 启动服务

```bash
# 后端
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8010

# 前端
cd frontend
npm run dev
```

### 测试流式响应

1. 登录系统
2. 选择 2 个平台，每平台 2 个变体
3. 点击生成
4. 观察结果渐进出现

**预期行为：**
- 首个变体在 4-7 秒内出现
- 后续变体陆续到达
- 不需要等待所有结果

## 技术细节

### SSE vs WebSocket

**为什么选择 SSE？**

| 特性 | SSE | WebSocket |
|------|-----|-----------|
| 方向 | 单向（服务器→客户端） | 双向 |
| 协议 | HTTP | 专用协议 |
| 实现复杂度 | 简单 | 复杂 |
| 自动重连 | 是 | 需手动实现 |
| 适用场景 | 服务器推送 | 实时双向通信 |

**结论：** 文案生成是单向推送场景，SSE 完全满足需求且更简单。

### 错误处理

**1. 部分失败策略**

当前实现：任何变体失败都会发送 error 事件，但不影响其他变体继续生成。

**改进建议：**
```python
# 可以在 error 事件中包含更多信息
yield {
    "type": "error",
    "platform": platform,
    "variant_index": idx,
    "message": error,
    "is_fatal": False  # 是否致命错误
}
```

**2. 超时处理**

```python
# config.py
llm_request_timeout: float = 30.0  # 单个请求超时
stream_total_timeout: float = 120.0  # 整个流式请求超时
```

**3. 网络中断恢复**

前端可以添加自动重连逻辑：

```typescript
let retryCount = 0;
const maxRetries = 3;

async function generateWithRetry(req: GenerateRequest) {
  try {
    await generateStream(req, onVariant, onComplete, onError);
  } catch (err) {
    if (retryCount < maxRetries) {
      retryCount++;
      setTimeout(() => generateWithRetry(req), 2000);
    } else {
      setError("网络连接失败，请稍后重试");
    }
  }
}
```

## 监控与调试

### 后端日志

添加日志跟踪流式生成：

```python
import logging

logger = logging.getLogger(__name__)

async def create_generation_stream(...):
    logger.info(f"Starting stream for request: {req.topic}")
    
    for variant in variants:
        logger.info(f"Yielding variant {variant.id}")
        yield {...}
    
    logger.info("Stream completed")
```

### 前端调试

在浏览器开发者工具中：

1. **Network 面板**：查看 `generate-stream` 请求
2. **EventStream 类型**：可以看到实时接收的事件
3. **Console**：查看解析的事件数据

## 兼容性

### 浏览器支持

SSE 在所有现代浏览器中都有良好支持：
- Chrome/Edge: ✅
- Firefox: ✅
- Safari: ✅
- IE11: ❌（不支持）

### 降级策略

如果需要支持旧浏览器，可以保留原始的批量 API：

```typescript
// 检测浏览器支持
const supportsStreaming = typeof ReadableStream !== 'undefined';

if (supportsStreaming) {
  await generateStream(req, ...);
} else {
  // 降级到批量API
  const result = await generate(req);
  setCurrentResult(result);
}
```

## 性能优化建议

### 1. 减少事件大小

只发送必要字段：

```python
# 只在最后发送完整数据，中间事件精简
yield {
    "type": "variant",
    "id": variant.id,
    "text": variant.final_text,  # 只发送文本
}
```

### 2. 压缩响应

```python
# main.py
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### 3. 限制并发连接

```python
# config.py
max_concurrent_streams: int = 10  # 限制同时流式请求数
```

## 下一步改进

- [ ] 添加进度百分比显示
- [ ] 支持取消正在进行的生成
- [ ] 添加生成耗时统计
- [ ] 实现请求队列管理
- [ ] 添加速率限制保护

## 故障排查

### 问题1：前端收不到数据

**检查：**
1. 后端是否正确启动在 8010 端口
2. CORS 配置是否包含前端地址
3. 浏览器控制台是否有错误

### 问题2：数据延迟很高

**检查：**
1. nginx/代理是否启用了缓冲（需要禁用）
2. LLM API 响应是否正常
3. 网络延迟情况

### 问题3：中途断开连接

**检查：**
1. 请求超时设置
2. 代理服务器超时配置
3. 客户端网络稳定性

## 总结

流式响应显著提升了用户体验：
- ✅ 首次内容时间从 20秒降至 4秒
- ✅ 渐进式呈现减少等待焦虑
- ✅ 实现简单，维护成本低
- ✅ 与并发优化完美配合

**建议：** 将流式 API 设为默认，保留批量 API 作为降级方案。
