# 用户登录功能说明

## 功能概述

已为AI社交文案生成助手项目的前后端添加了完整的用户登录功能。

## 后端实现

### 1. 新增依赖（requirements.txt）
- `python-jose[cryptography]` - JWT令牌生成和验证
- `passlib[bcrypt]` - 密码哈希和验证

### 2. 数据模型（app/models.py）
新增 `User` 模型：
- id: 用户ID
- username: 用户名（唯一）
- hashed_password: 哈希密码
- full_name: 全名
- is_active: 是否激活
- created_at: 创建时间

### 3. 认证模块（app/auth.py）
提供以下功能：
- `verify_password()` - 验证密码
- `get_password_hash()` - 生成密码哈希
- `create_access_token()` - 创建JWT令牌
- `authenticate_user()` - 用户认证
- `get_current_user()` - 获取当前登录用户
- `get_current_active_user()` - 获取当前激活用户（依赖注入）

### 4. 配置更新（app/config.py）
新增JWT配置：
- `jwt_secret_key` - JWT密钥（生产环境需修改）
- `jwt_algorithm` - 加密算法（HS256）
- `jwt_access_token_expire_minutes` - 令牌过期时间（30分钟）

### 5. 认证路由（app/routers/auth.py）
提供以下接口：
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/me` - 获取当前用户信息
- `POST /api/auth/create-user` - 创建用户（仅供内部使用）

### 6. 路由保护
所有业务路由已添加认证依赖：
- `/api/generate` - 生成文案
- `/api/history` - 历史记录
- `/api/variants/{id}/rate` - 评分
- `/api/documents/*` - 知识库管理

## 前端实现

### 1. 类型定义（src/types.ts）
新增接口：
- `LoginRequest` - 登录请求
- `Token` - 令牌响应
- `UserOut` - 用户信息

### 2. API模块更新（src/api.ts）
- 新增 `login()` - 登录接口
- 新增 `getCurrentUser()` - 获取用户信息接口
- 新增 `getToken()`、`setToken()`、`removeToken()` - Token管理
- 更新 `getHeaders()` - 自动添加Authorization头
- 更新 `handleResponse()` - 处理401未授权响应

### 3. 登录组件（src/components/LoginForm.tsx）
- 用户名和密码输入表单
- 表单验证
- 错误提示
- 加载状态

### 4. 主应用更新（src/App.tsx）
- 添加认证状态管理
- 启动时检查登录状态
- 未登录显示登录页面
- 登录后显示主界面
- 顶部导航栏添加用户信息和退出按钮

## 使用说明

### 启动后端
```bash
cd backend
source ../.venv/Scripts/activate  # Windows: ..\.venv\Scripts\activate
uvicorn app.main:app --reload
```

### 创建测试用户
已创建默认测试用户：
- 用户名: `admin`
- 密码: `admin123`

### 启动前端
```bash
cd frontend
npm install
npm run dev
```

### 登录测试
1. 访问 http://localhost:5173
2. 输入用户名: admin
3. 输入密码: admin123
4. 点击登录

## 安全说明

### 生产环境配置
在 `backend/.env` 文件中修改以下配置：
```
JWT_SECRET_KEY=your-very-secure-random-secret-key-here
```

生成安全的密钥：
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 注意事项
1. `/api/auth/create-user` 接口应在生产环境中移除或添加管理员权限检查
2. Token默认30分钟过期，可根据需求调整
3. 密码使用bcrypt加密，安全性较高
4. 所有API请求都需要携带有效的JWT令牌

## API认证流程

1. 用户提交用户名和密码到 `/api/auth/login`
2. 后端验证用户名和密码
3. 验证成功返回JWT令牌
4. 前端将令牌存储在localStorage
5. 后续请求在Authorization头中携带令牌
6. 后端验证令牌并返回用户信息
7. 令牌过期或无效时返回401，前端跳转登录页

## 技术栈

### 后端
- FastAPI - Web框架
- SQLAlchemy - ORM
- python-jose - JWT处理
- passlib + bcrypt - 密码加密

### 前端
- React + TypeScript
- Fetch API - HTTP请求
- localStorage - Token存储
