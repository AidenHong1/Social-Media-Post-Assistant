# CORS 配置验证指南

## 当前配置状态

### 1. CORS 设置（backend/app/main.py）

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # 从 .env 读取
    allow_credentials=True,
    allow_methods=["*"],                  # 允许所有 HTTP 方法
    allow_headers=["*"],                  # 允许所有请求头
)
```

### 2. 环境变量配置（backend/.env）

```bash
CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173","http://localhost:5174","http://127.0.0.1:5174"]
```

✅ 已包含前端地址 `http://localhost:5173`

### 3. 图片生成配置

```bash
IMAGE_GENERATION_ENABLED=true          # ✅ 已启用
IMAGE_RATE_LIMIT_INTERVAL=1.0         # ✅ 速率限制：1秒
IMAGE_MAX_RETRIES=3                    # ✅ 最大重试：3次
```

## CORS 错误的常见原因

### 问题 1: 后端服务未运行
**症状**: 浏览器控制台显示 CORS 错误
**原因**: 后端没有启动，请求根本没有到达服务器

**解决方法**:
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 问题 2: 后端端口不正确
**症状**: 前端请求 `http://localhost:8000`，但后端在其他端口运行

**验证方法**:
```bash
# 检查 8000 端口是否被占用
netstat -ano | findstr :8000

# 或者使用 curl 测试
curl http://localhost:8000/api/health
```

### 问题 3: 配置未生效
**症状**: 修改了 `.env` 但 CORS 错误仍然存在

**解决方法**: 重启后端服务
```bash
# Ctrl+C 停止服务
# 然后重新启动
uvicorn app.main:app --reload
```

### 问题 4: 预检请求（OPTIONS）失败
**症状**: 浏览器发送 OPTIONS 请求但被拦截

**当前配置**: ✅ 已设置 `allow_methods=["*"]`，应该支持 OPTIONS

## 验证步骤

### 步骤 1: 确认后端运行

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

预期输出:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 步骤 2: 测试健康检查端点

```bash
curl http://localhost:8000/api/health
```

预期输出:
```json
{"status":"ok"}
```

### 步骤 3: 测试 CORS 预检请求

```bash
curl -X OPTIONS http://localhost:8000/api/images/auto-for-variant \
  -H "Origin: http://localhost:5173" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type,authorization" \
  -v
```

预期响应头应包含:
```
Access-Control-Allow-Origin: http://localhost:5173
Access-Control-Allow-Methods: DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT
Access-Control-Allow-Headers: *
Access-Control-Allow-Credentials: true
```

### 步骤 4: 在浏览器中测试

打开浏览器开发者工具（F12）：

1. **Network 标签页**
   - 查看请求是否发送到 `http://localhost:8000`
   - 检查响应头是否包含 `Access-Control-Allow-Origin`

2. **Console 标签页**
   - 查看详细的 CORS 错误信息

## 常见错误信息和解决方案

### 错误 1: "No 'Access-Control-Allow-Origin' header"

```
Access to fetch at 'http://localhost:8000/api/images/auto-for-variant' 
from origin 'http://localhost:5173' has been blocked by CORS policy: 
No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

**可能原因**:
- ✅ 后端未运行
- ✅ 后端崩溃或抛出异常
- ✅ 请求到达错误的端点

**解决步骤**:
1. 确认后端服务正在运行
2. 检查后端日志是否有错误
3. 验证请求 URL 是否正确

### 错误 2: "Response to preflight request doesn't pass"

```
Access to fetch has been blocked by CORS policy: 
Response to preflight request doesn't pass access control check
```

**可能原因**:
- OPTIONS 请求返回非 2xx 状态码
- 缺少必要的 CORS 响应头

**解决方法**: 当前配置应该已经处理，如果仍有问题，请检查是否有其他中间件干扰

### 错误 3: "Credentials flag is true, but 'Access-Control-Allow-Credentials' header is ''"

**当前配置**: ✅ 已设置 `allow_credentials=True`

## 前端配置检查

确保前端发送请求时使用正确的 URL：

```javascript
// ✅ 正确
const response = await fetch('http://localhost:8000/api/images/auto-for-variant', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify(data)
});

// ❌ 错误 - 缺少端口号
const response = await fetch('http://localhost/api/images/auto-for-variant', ...);

// ❌ 错误 - 使用了 HTTPS
const response = await fetch('https://localhost:8000/api/images/auto-for-variant', ...);
```

## 快速诊断命令

运行这些命令快速诊断问题：

```bash
# 1. 检查后端是否运行
curl http://localhost:8000/api/health

# 2. 检查端口占用
netstat -ano | findstr :8000

# 3. 测试 OPTIONS 请求
curl -X OPTIONS http://localhost:8000/api/images/auto-for-variant \
  -H "Origin: http://localhost:5173" \
  -v 2>&1 | grep -i "access-control"

# 4. 查看后端日志
cd backend
uvicorn app.main:app --reload --log-level debug
```

## 如果问题仍然存在

1. **重启所有服务**
   ```bash
   # 停止后端（Ctrl+C）
   # 停止前端（Ctrl+C）
   
   # 重新启动后端
   cd backend
   uvicorn app.main:app --reload
   
   # 重新启动前端
   cd frontend
   npm run dev
   ```

2. **清除浏览器缓存**
   - 打开开发者工具（F12）
   - 右键点击刷新按钮
   - 选择"清空缓存并硬性重新加载"

3. **检查防火墙设置**
   - 确保防火墙允许 8000 端口

4. **使用不同的浏览器**
   - 尝试 Chrome、Firefox 或 Edge
   - 某些浏览器扩展可能干扰 CORS

## 调试技巧

### 启用详细日志

修改 `backend/app/main.py`，临时添加日志中间件：

```python
@app.middleware("http")
async def log_requests(request, call_next):
    print(f"Request: {request.method} {request.url}")
    print(f"Origin: {request.headers.get('origin')}")
    response = await call_next(request)
    print(f"Response status: {response.status_code}")
    return response
```

### 浏览器开发者工具

1. 打开 Network 标签
2. 勾选"Preserve log"
3. 观察请求和响应的详细信息
4. 特别注意：
   - Request URL
   - Request Method
   - Status Code
   - Response Headers

## 总结

✅ **当前 CORS 配置是正确的**

如果仍然遇到 CORS 错误，最可能的原因是：
1. 后端服务未运行或崩溃
2. 请求 URL 不正确
3. 配置修改后未重启服务

**建议的标准启动流程**:

```bash
# Terminal 1 - 后端
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - 前端
cd frontend
npm run dev
```

然后在浏览器访问 `http://localhost:5173`
