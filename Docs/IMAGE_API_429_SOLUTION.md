# 图片生成 API 429 错误解决方案

## 问题描述

在使用图片生成功能时遇到 `HTTP 429 Too Many Requests` 错误：

```
httpx.HTTPStatusError: Client error '429 Too Many Requests' for url 'https://linoapi.com.cn/v1/images/generations'
```

## 原因分析

HTTP 429 错误表示超过了 API 提供商的速率限制（Rate Limit），常见原因：

1. **请求频率过高**：短时间内发送了太多请求
2. **API 配额限制**：达到了账户的每日/每小时配额上限
3. **免费套餐限制**：免费账户通常有更严格的速率限制
4. **并发请求过多**：同时发送多个图片生成请求

## 已实现的解决方案

### 1. 自动重试机制

当遇到 429 错误时，系统会自动重试：
- 默认最大重试 **3 次**
- 使用**指数退避**策略：每次等待时间递增（2秒 → 4秒 → 8秒）
- 如果 API 返回 `Retry-After` 头，会遵循该时间

### 2. 速率限制

在每次请求之前强制等待：
- 默认请求间隔：**1 秒**
- 确保不会过快发送连续请求
- 防止触发 API 的速率限制

### 3. 详细日志

系统会记录详细的错误和重试信息：
```
速率限制: 等待 0.85 秒
收到 429 错误，第 1/3 次尝试，等待 2 秒后重试...
图片生成成功: abc123def456.png
```

## 配置选项

在 `.env` 文件中可以调整以下参数：

```bash
# 请求间隔（秒）- 增大此值可降低请求频率
IMAGE_RATE_LIMIT_INTERVAL=1.0

# 最大重试次数 - 遇到 429 错误时的重试次数
IMAGE_MAX_RETRIES=3
```

### 推荐配置

根据您的 API 套餐调整配置：

**免费套餐/受限账户**：
```bash
IMAGE_RATE_LIMIT_INTERVAL=2.0  # 增加间隔到 2 秒
IMAGE_MAX_RETRIES=5            # 增加重试次数
```

**付费套餐/高配额**：
```bash
IMAGE_RATE_LIMIT_INTERVAL=0.5  # 可以更快
IMAGE_MAX_RETRIES=3            # 默认即可
```

## 使用建议

### 1. 检查 API 配额

联系您的 API 提供商（linoapi.com.cn）确认：
- 每分钟/每小时的请求限制
- 账户当前的配额使用情况
- 是否需要升级到更高级别的套餐

### 2. 避免批量操作

不要在短时间内生成大量图片：
```python
# ❌ 避免这样做
for i in range(10):
    await image_service.generate_image(prompt)

# ✅ 应该这样做
for i in range(10):
    await image_service.generate_image(prompt)
    await asyncio.sleep(2)  # 额外等待
```

### 3. 监控日志

启动应用时注意观察日志输出：
- 如果频繁看到 "速率限制: 等待" 消息，说明系统在正常工作
- 如果看到 "收到 429 错误"，考虑增加 `IMAGE_RATE_LIMIT_INTERVAL`

### 4. 缓存生成结果

对于相同的 prompt，考虑缓存已生成的图片：
- 避免重复生成相同内容
- 节省 API 配额和时间

## 错误处理

如果重试多次后仍然失败，系统会抛出清晰的错误消息：

```
API 请求限制: 已达到速率限制，重试 3 次后仍失败。
请稍后再试或联系 API 提供商检查配额。

建议:
1) 减少请求频率
2) 检查 API 配额
3) 稍后再试
```

## 故障排查步骤

1. **确认 API 密钥有效**
   ```bash
   # 检查 .env 文件
   cat backend/.env | grep IMAGE_API_KEY
   ```

2. **测试 API 连接**
   ```bash
   curl -H "Authorization: Bearer YOUR_API_KEY" \
        https://linoapi.com.cn/v1/models
   ```

3. **查看应用日志**
   ```bash
   # 启动应用并观察输出
   cd backend
   uvicorn app.main:app --reload
   ```

4. **调整配置后重启**
   ```bash
   # 修改 .env 文件后需要重启应用
   # Ctrl+C 停止，然后重新启动
   ```

## 技术实现细节

### 重试逻辑

```python
for attempt in range(max_retries):
    try:
        await self._rate_limit()  # 强制等待
        resp = await client.post(...)
        
        if resp.status_code == 429:
            # 检查 Retry-After 头
            wait_time = resp.headers.get("Retry-After") or (2 ** attempt * 2)
            await asyncio.sleep(wait_time)
            continue
            
        return result
    except Exception as e:
        if attempt == max_retries - 1:
            raise
```

### 速率限制

```python
async def _rate_limit(self):
    elapsed = time.time() - self._last_request_time
    if elapsed < self._min_request_interval:
        await asyncio.sleep(self._min_request_interval - elapsed)
    self._last_request_time = time.time()
```

## 更新日志

- **2026-07-29**: 添加自动重试和速率限制功能
- 支持可配置的重试次数和请求间隔
- 改进错误消息和日志输出

## 联系支持

如果问题持续存在：
1. 检查 linoapi.com.cn 的服务状态
2. 联系 API 提供商技术支持
3. 考虑切换到其他 DALL-E 3 兼容的 API 服务商
