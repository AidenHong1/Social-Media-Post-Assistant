# Z-Image-Turbo 阿里云百炼配置指南

## 配置完成

### 已实现的功能

✅ **异步任务支持**：自动提交任务并轮询结果  
✅ **同步/异步兼容**：自动检测 API 响应模式  
✅ **超时重试**：最多重试 3 次，指数退避  
✅ **速率限制**：请求间隔 1 秒，防止 429 错误  
✅ **详细日志**：记录任务状态和进度  

### 代码改动

1. **`backend/app/services/image_service.py`**：重写为阿里云 DashScope API
   - 支持异步任务提交和轮询
   - 自动处理 task_id 和任务状态
   - 分离下载逻辑到独立方法

2. **`backend/.env`**：更新配置
   - `IMAGE_API_BASE_URL`: `https://dashscope.aliyuncs.com/api/v1`
   - `IMAGE_MODEL`: `z-image-turbo`
   - 需要填入阿里云 API Key

## 配置步骤

### 1. 获取阿里云 API Key

访问 [阿里云百炼控制台](https://bailian.console.aliyun.com/)：

1. 登录阿里云账号
2. 进入"API-KEY 管理"
3. 创建新的 API Key 或使用现有的
4. 复制 API Key（格式：`sk-xxxxxxxxxxxxxxxx`）

### 2. 更新 .env 配置

编辑 `backend/.env` 文件：

```bash
# 将 your-aliyun-dashscope-api-key-here 替换为实际的 API Key
IMAGE_API_KEY=sk-your-actual-api-key-here
IMAGE_API_BASE_URL=https://dashscope.aliyuncs.com/api/v1
IMAGE_MODEL=z-image-turbo
IMAGE_GENERATION_ENABLED=true
IMAGE_RATE_LIMIT_INTERVAL=1.0
IMAGE_MAX_RETRIES=3
```

### 3. 重启后端服务

```bash
cd backend
# 停止现有服务 (Ctrl+C)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API 调用流程

### 异步模式（推荐）

```
1. 提交任务
   POST /services/aigc/image-synthesis/generation
   返回: { "output": { "task_id": "xxx" } }

2. 轮询任务状态 (每 2 秒)
   GET /services/aigc/image-synthesis/generation/{task_id}
   
3. 任务状态
   - PENDING: 排队中
   - RUNNING: 生成中
   - SUCCEEDED: 成功 → 获取图片 URL
   - FAILED: 失败 → 返回错误

4. 下载图片
   GET {image_url}
   保存到本地: storage/images/{uuid}.png
```

### 同步模式（备用）

如果 API 直接返回图片 URL（不返回 task_id），则跳过轮询直接下载。

## 支持的图片尺寸

| 前端传入      | 转换为 DashScope 格式 | 说明           |
|---------------|------------------------|----------------|
| 1024x1024     | 1024*1024              | 正方形（默认） |
| 1024x1792     | 720*1280               | 竖屏           |
| 1792x1024     | 1280*720               | 横屏           |

Z-Image-Turbo 支持的尺寸格式使用 `*` 而不是 `x`。

## 日志输出示例

### 成功场景

```
INFO: 开始生成图片 (尝试 1/3)
INFO: 任务已提交: task-abc123，开始轮询结果...
INFO: 任务进行中... (1/60)
INFO: 任务进行中... (2/60)
INFO: 图片生成成功，开始下载: https://dashscope-result-bj.oss...
INFO: 图片下载并保存成功: abc123def456.png (245678 字节)
```

### 重试场景

```
ERROR: 请求超时 (第 1/3 次)
INFO: 等待 2 秒后重试...
INFO: 开始生成图片 (尝试 2/3)
INFO: 任务已提交: task-def456，开始轮询结果...
```

### 429 错误

```
WARNING: 收到 429 错误，等待 4 秒后重试...
INFO: 开始生成图片 (尝试 2/3)
```

## 配置参数说明

### IMAGE_RATE_LIMIT_INTERVAL

请求间隔时间（秒）。建议：
- **免费套餐**: 2.0 秒
- **付费套餐**: 1.0 秒

### IMAGE_MAX_RETRIES

遇到错误时的最大重试次数。建议：
- **稳定网络**: 3 次
- **不稳定网络**: 5 次

### 轮询配置（代码中）

```python
max_polls = 60         # 最多轮询 60 次
poll_interval = 2      # 每 2 秒轮询一次
# 最长等待时间 = 60 * 2 = 120 秒
```

如需调整，编辑 `image_service.py` 第 147-148 行。

## 错误处理

### 常见错误

| 错误代码 | 原因                     | 解决方法                          |
|----------|--------------------------|-----------------------------------|
| 401      | API Key 无效或过期       | 检查 IMAGE_API_KEY 是否正确       |
| 429      | 请求过多                 | 增加 IMAGE_RATE_LIMIT_INTERVAL    |
| 504      | 轮询超时                 | 检查网络连接或增加 max_polls      |
| 400      | 参数错误（如尺寸不支持） | 检查 prompt 和 size 参数          |

### task_status = FAILED

任务失败的常见原因：
- Prompt 包含敏感内容（违规检测）
- 参数不合法
- 账户余额不足

查看后端日志中的 `error_msg` 获取详细信息。

## 与原实现的区别

| 特性           | 原实现 (OpenAI 兼容)    | 新实现 (阿里云 DashScope)   |
|----------------|-------------------------|------------------------------|
| 调用方式       | 同步                    | 异步（任务轮询）             |
| API 格式       | /images/generations     | /image-synthesis/generation  |
| 响应方式       | 直接返回图片 URL        | 返回 task_id，需轮询         |
| 尺寸格式       | 1024x1024 (x)           | 1024*1024 (*)                |
| 超时时间       | 180 秒（生成）          | 120 秒（轮询总时长）         |
| 请求头         | Authorization: Bearer   | Authorization: Bearer + X-DashScope-Async |

## 测试步骤

### 1. 验证配置

```bash
cd backend
python -c "from app.config import settings; print('API Base URL:', settings.image_api_base_url); print('Model:', settings.image_model); print('Enabled:', settings.image_generation_enabled)"
```

预期输出：
```
API Base URL: https://dashscope.aliyuncs.com/api/v1
Model: z-image-turbo
Enabled: True
```

### 2. 启动服务

```bash
uvicorn app.main:app --reload --log-level info
```

### 3. 前端测试

1. 访问 `http://localhost:5173`
2. 登录并生成帖子变体
3. 点击"生成图片"按钮
4. 观察：
   - 前端显示加载状态（可能需要 10-30 秒）
   - 后端日志显示任务提交和轮询进度
   - 图片成功显示或错误提示

### 4. 手动 API 测试

使用 curl 测试（需要替换 API Key）：

```bash
curl -X POST https://dashscope.aliyuncs.com/api/v1/services/aigc/image-synthesis/generation \
  -H "Authorization: Bearer sk-your-api-key" \
  -H "Content-Type: application/json" \
  -H "X-DashScope-Async: enable" \
  -d '{
    "model": "z-image-turbo",
    "input": {
      "prompt": "a beautiful sunset over mountains"
    },
    "parameters": {
      "size": "1024*1024",
      "n": 1
    }
  }'
```

## 性能特点

### Z-Image-Turbo 优势

- **快速生成**: 单张 1024x1024 图片约 2-3 秒
- **低参数**: 约 6B 参数，资源消耗低
- **中文支持**: 原生支持中英文 prompt
- **开源协议**: Apache 2.0

### 预期性能

- **提交任务**: < 1 秒
- **图片生成**: 2-5 秒
- **轮询延迟**: 2-10 秒（取决于轮询次数）
- **下载图片**: 1-3 秒
- **总耗时**: 5-20 秒

## 故障排查

### 问题：API Key 错误

```
HTTP 401: Unauthorized
```

**解决**：
1. 确认 API Key 格式正确（`sk-` 开头）
2. 检查 API Key 是否激活
3. 确认账户有图片生成权限

### 问题：轮询超时

```
图片生成超时: 轮询 120 秒后任务仍未完成
```

**解决**：
1. 检查阿里云服务状态
2. 增加 `max_polls` 值（代码中）
3. 检查网络连接

### 问题：任务失败

```
任务失败: content security violation
```

**解决**：
- Prompt 可能包含敏感内容
- 修改 prompt 或使用更通用的描述
- 查看阿里云内容安全政策

## 成本估算

Z-Image-Turbo 定价（截至 2026 年，以阿里云官网为准）：

- **按次计费**: 约 ¥0.02-0.05/张
- **包月套餐**: 可能有优惠

建议在阿里云控制台查看最新价格。

## 总结

✅ 配置已完成，需要的操作：

1. **获取阿里云 API Key**（最重要）
2. **填入 `.env` 文件**
3. **重启后端服务**
4. **测试图片生成功能**

所有代码改动已完成，支持异步任务轮询，具有完善的错误处理和重试机制。
