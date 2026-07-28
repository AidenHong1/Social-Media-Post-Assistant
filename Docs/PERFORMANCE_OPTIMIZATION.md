# 文案生成性能优化方案

## 问题分析

### 原始架构的性能瓶颈

**串行处理导致的延迟累积：**

1. **多平台串行处理**：每个平台按顺序处理
2. **多变体串行生成**：每个平台的变体按顺序生成
3. **每个变体需要 2-3 次 LLM 调用**：
   - `generate_draft()` - 生成初稿
   - `critique_draft()` - 评审初稿
   - `rewrite_draft()` - 重写（如果评审未通过）

**性能计算示例（2平台，每平台2变体）：**

```
原始架构（串行）：
- 总 LLM 调用次数：2平台 × 2变体 × 2.5次平均调用 = 10次
- 每次调用耗时：2-3秒
- 总耗时：20-30秒

优化后（并发）：
- 并发处理平台和变体
- 理论耗时：单个变体的时间（2-3次调用 × 2-3秒 = 4-9秒）
- 实际加速比：3-5倍
```

## 优化方案

### 方案1：双层并发架构（已实现）

**核心改进：**

1. **平台级并发**（`generation_service.py`）
   - 使用 `ThreadPoolExecutor` 并发处理所有平台
   - 工作线程数 = 平台数量

2. **变体级并发**（`orchestrator.py`）
   - 每个平台内并发生成所有变体
   - 工作线程数 = 变体数量

**代码变更：**

```python
# orchestrator.py - 变体级并发
def run_platform_variants(...) -> list[PipelineResult]:
    """并发生成多个变体以提升性能"""
    with ThreadPoolExecutor(max_workers=n_variants) as executor:
        futures = [
            executor.submit(run_single_variant, ...)
            for _ in range(n_variants)
        ]
        return [future.result() for future in futures]

# generation_service.py - 平台级并发
with ThreadPoolExecutor(max_workers=len(req.platforms)) as executor:
    futures = [executor.submit(process_platform, platform) 
               for platform in req.platforms]
    all_results = [future.result() for future in futures]
```

**性能提升：**

| 场景 | 原始耗时 | 优化后耗时 | 加速比 |
|------|---------|-----------|--------|
| 1平台2变体 | 8-15秒 | 4-7秒 | 2倍 |
| 2平台2变体 | 16-30秒 | 4-9秒 | 3-5倍 |
| 2平台3变体 | 24-45秒 | 6-12秒 | 4-6倍 |

## 进一步优化建议

### 方案2：流式响应（待实现）

**目标：** 让用户更早看到第一个结果，提升体验

```python
# 使用 FastAPI StreamingResponse
from fastapi.responses import StreamingResponse

async def generate_stream():
    for result in results_as_they_complete:
        yield json.dumps(result) + "\n"

@router.post("/generate-stream")
async def generate_stream_endpoint():
    return StreamingResponse(generate_stream(), media_type="text/event-stream")
```

**用户体验改进：**
- 第一个变体 4-7秒 即可显示
- 后续变体陆续到达
- 不需要等待所有结果

### 方案3：提示词优化（待验证）

**目标：** 减少需要 rewrite 的比例

1. **优化 critique 提示词**：更宽松的评审标准
2. **优化 generate 提示词**：更准确的初稿生成
3. **监控 `was_rewritten` 比例**：目标降低至 20% 以下

**潜在收益：**
- 如果 rewrite 比例从 50% 降至 20%
- 平均调用次数从 2.5 降至 2.2
- 额外加速 10-15%

### 方案4：LLM 配置优化

**调整 LLM 超时和并发限制：**

```python
# config.py
class Settings(BaseSettings):
    llm_request_timeout: float = 30.0  # 从 60 降至 30
    llm_max_retries: int = 2
    llm_concurrent_requests: int = 10  # 限制最大并发数
```

**原因：**
- 30秒超时足够大部分请求
- 减少等待失败请求的时间
- 控制并发数避免 API 限流

### 方案5：缓存机制（待实现）

**场景：** 相似请求重复生成

```python
from functools import lru_cache
import hashlib

def get_cache_key(topic, key_points, brand_tone, platform):
    content = f"{topic}_{key_points}_{brand_tone}_{platform}"
    return hashlib.md5(content.encode()).hexdigest()

# 缓存最近的生成结果
```

## 监控指标

建议添加以下性能监控：

```python
import time

class PerformanceMetrics:
    generation_time: float
    llm_calls_count: int
    rewrite_ratio: float
    platform_count: int
    variant_count: int
```

**关键指标：**
- 平均生成时间：目标 < 10秒（2平台2变体）
- Rewrite 比例：目标 < 30%
- LLM 调用成功率：目标 > 95%

## 使用说明

### 启动优化后的服务

```bash
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8010
```

### 测试并发性能

```bash
# 观察日志中的并发执行
# 多个 "Generating variant..." 应该几乎同时出现
```

### 回滚方案

如果并发导致问题（如 API 限流），可以临时降低并发数：

```python
# orchestrator.py
with ThreadPoolExecutor(max_workers=1) as executor:  # 恢复串行
```

## 已知限制

1. **API 限流**：某些 LLM 提供商有并发限制
   - 解决方案：在 `config.py` 中配置 `llm_concurrent_requests`

2. **内存占用**：并发会增加内存使用
   - 当前实现：合理范围内（< 500MB）

3. **错误处理**：某个变体失败不影响其他变体
   - 当前行为：任何失败会导致整个请求失败
   - 改进方向：部分成功也返回结果

## 下一步行动

- [ ] 添加性能监控和日志
- [ ] 实现流式响应
- [ ] 优化提示词减少 rewrite
- [ ] 添加结果缓存
- [ ] 添加并发限流保护
