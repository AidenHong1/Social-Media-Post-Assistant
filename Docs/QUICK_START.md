# 快速启动指南

## 安装依赖

### 后端依赖
```bash
cd backend
pip install -r requirements.txt
```

**重要**: 必须使用bcrypt 4.0.1版本，bcrypt 5.x与passlib不兼容。

或者手动安装：
```bash
pip install python-jose passlib bcrypt==4.0.1 cryptography
```

或者使用虚拟环境：
```bash
# Windows
.venv\Scripts\activate
pip install python-jose passlib bcrypt cryptography

# Linux/Mac
source .venv/bin/activate
pip install python-jose passlib bcrypt cryptography
```

### 前端依赖
```bash
cd frontend
npm install
```

## 启动服务

### 1. 启动后端
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端将运行在: http://localhost:8000

### 2. 启动前端
```bash
cd frontend
npm run dev
```

前端将运行在: http://localhost:5173

## 登录测试

访问 http://localhost:5173 并使用以下凭据登录：

- **用户名**: `admin`
- **密码**: `admin123`

## 测试用户已创建

系统已自动创建测试用户，可直接使用上述凭据登录。

## API文档

启动后端后，访问以下地址查看API文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 主要功能

### 认证相关
- ✅ 用户登录
- ✅ JWT令牌管理
- ✅ 自动Token刷新检查
- ✅ 退出登录
- ✅ 401错误自动跳转登录页

### 已保护的API端点
- ✅ `/api/generate` - 生成文案
- ✅ `/api/history` - 历史记录
- ✅ `/api/history/{id}` - 获取单条记录
- ✅ `/api/variants/{id}/rate` - 评分
- ✅ `/api/documents/*` - 知识库管理

## 创建新用户（可选）

如需创建新用户，可以：

### 方法1: 使用API（临时开放）
```bash
curl -X POST "http://localhost:8000/api/auth/create-user" \
  -H "Content-Type: application/json" \
  -d '{"username": "user1", "password": "password123", "full_name": "用户1"}'
```

### 方法2: 使用Python脚本
创建 `create_new_user.py`:
```python
import requests

response = requests.post(
    "http://localhost:8000/api/auth/create-user",
    json={
        "username": "user1",
        "password": "password123",
        "full_name": "用户1"
    }
)
print(response.json())
```

**注意**: 生产环境应移除或保护 `/api/auth/create-user` 接口！

## 故障排查

### 问题1: 后端启动失败
检查是否安装了所有依赖：
```bash
pip list | grep -E "python-jose|passlib|bcrypt"
```

### 问题2: 前端无法连接后端
检查 CORS 配置，确保 `backend/app/config.py` 中的 `cors_origins` 包含前端地址：
```python
cors_origins: list[str] = ["http://localhost:5173"]
```

### 问题3: 登录后立即退出
检查浏览器控制台，可能是Token存储问题或API返回401。

### 问题4: bcrypt相关错误
**最常见问题**: bcrypt版本不兼容。

**错误示例**:
```
ValueError: password cannot be longer than 72 bytes
AttributeError: module 'bcrypt' has no attribute '__about__'
```

**解决方案**:
```bash
pip uninstall bcrypt
pip install bcrypt==4.0.1
```

然后重新创建用户：
```bash
cd backend
source ../.venv/Scripts/activate  # Windows: ..\.venv\Scripts\activate
python -c "
from app.db import SessionLocal
from app.models import User
from app.auth import get_password_hash

db = SessionLocal()
old_user = db.query(User).filter(User.username == 'admin').first()
if old_user:
    db.delete(old_user)
    db.commit()

new_user = User(
    username='admin',
    hashed_password=get_password_hash('admin123'),
    full_name='管理员',
    is_active=True
)
db.add(new_user)
db.commit()
db.close()
print('用户创建成功')
"
```

## 生产环境部署

### 必须修改的配置

1. **JWT密钥** (`backend/.env`):
```
JWT_SECRET_KEY=your-secure-random-key-here
```

生成安全密钥：
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

2. **移除或保护创建用户接口**:
在 `backend/app/routers/auth.py` 中删除或添加管理员权限检查到 `create_user` 函数。

3. **CORS配置**:
更新 `backend/app/config.py` 中的 `cors_origins` 为实际的前端域名。

4. **HTTPS**:
生产环境必须使用HTTPS以保护JWT令牌传输。

## 项目结构

```
backend/
├── app/
│   ├── auth.py              # 认证模块
│   ├── config.py            # 配置（含JWT配置）
│   ├── main.py              # 主应用（已注册auth路由）
│   ├── models.py            # 数据模型（含User模型）
│   └── routers/
│       ├── auth.py          # 认证路由
│       ├── generate.py      # 已添加认证
│       ├── history.py       # 已添加认证
│       ├── knowledge.py     # 已添加认证
│       └── variants.py      # 已添加认证
├── create_user_simple.py    # 用户创建脚本
└── requirements.txt         # 已更新依赖

frontend/
├── src/
│   ├── api.ts               # API模块（已添加认证）
│   ├── types.ts             # 类型定义（已添加认证类型）
│   ├── App.tsx              # 主应用（已集成登录）
│   └── components/
│       └── LoginForm.tsx    # 登录组件
```
