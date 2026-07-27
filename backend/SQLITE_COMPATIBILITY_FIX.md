# SQLite 扩展兼容性修复

## 问题描述

在某些环境下启动后端时会出现以下错误：

```
AttributeError: 'sqlite3.Connection' object has no attribute 'enable_load_extension'
```

## 根本原因

这个错误发生在以下情况：

1. **Python 发行版限制**：某些 Python 发行版（特别是从系统包管理器安装的）编译 SQLite 时禁用了扩展加载功能
2. **安全考虑**：某些环境出于安全原因禁用了动态加载扩展
3. **平台差异**：Windows、macOS、Linux 的不同发行版可能有不同的 SQLite 编译选项

## 受影响的功能

**sqlite-vec 扩展用于：**
- 向量相似度搜索
- 企业知识库的语义检索
- RAG（检索增强生成）功能

**如果扩展加载失败：**
- ✅ 核心文案生成功能**正常工作**
- ✅ 用户登录和认证**正常工作**
- ✅ 历史记录和评分**正常工作**
- ⚠️ 知识库上传和检索功能**降级**（不使用向量搜索）

## 修复方案

### 方案 1：优雅降级（已实现）

**修改内容：**

**1. `backend/app/db.py` - 扩展加载容错**

```python
@event.listens_for(engine, "connect")
def _load_sqlite_vec_extension(dbapi_conn, connection_record) -> None:
    """加载 sqlite-vec 扩展，如果环境不支持则跳过"""
    try:
        if not hasattr(dbapi_conn, "enable_load_extension"):
            warnings.warn("SQLite extension loading not supported...")
            return

        dbapi_conn.enable_load_extension(True)
        sqlite_vec.load(dbapi_conn)
        dbapi_conn.enable_load_extension(False)
    except AttributeError as e:
        warnings.warn(f"Failed to load sqlite-vec extension: {e}")
    except Exception as e:
        warnings.warn(f"Unexpected error loading sqlite-vec extension: {e}")
```

**特点：**
- ✅ 检测是否支持扩展加载
- ✅ 捕获所有异常，避免启动失败
- ✅ 发出警告但继续运行
- ✅ 应用在无向量搜索的情况下仍可用

**2. `backend/app/main.py` - 向量表创建容错**

```python
@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)

    # 尝试创建向量表，如果扩展未加载则跳过
    try:
        with engine.begin() as conn:
            conn.execute(
                text("CREATE VIRTUAL TABLE IF NOT EXISTS vec_chunks USING vec0(...)")
            )
    except Exception as e:
        warnings.warn(f"Failed to create vector table: {e}. Vector search disabled.")

    # 加载嵌入模型
    try:
        get_embedding_model()
    except Exception as e:
        warnings.warn(f"Failed to load embedding model: {e}")
```

**特点：**
- ✅ 向量表创建失败不影响启动
- ✅ 嵌入模型加载失败也不影响启动
- ✅ 应用可以在降级模式下运行

### 方案 2：使用支持扩展的 Python（推荐用于生产环境）

**对于 Linux（Ubuntu/Debian）：**

```bash
# 方法1：使用 pysqlite3-binary（推荐）
pip install pysqlite3-binary

# 方法2：从源码编译 Python
sudo apt-get install libsqlite3-dev
# 重新编译 Python 时会自动启用扩展支持
```

**对于 macOS：**

```bash
# Homebrew Python 通常已启用扩展支持
brew install python@3.12

# 或使用 pyenv
pyenv install 3.12.0
```

**对于 Windows：**

```bash
# 官方 Python.org 安装包通常支持扩展
# 下载并安装：https://www.python.org/downloads/

# 或使用 conda
conda install python=3.12
```

### 方案 3：使用 pysqlite3-binary（快速解决）

如果你需要向量搜索功能但当前环境不支持：

```bash
pip install pysqlite3-binary
```

然后在 `backend/app/db.py` 顶部添加：

```python
# 使用 pysqlite3-binary 替代内置 sqlite3
import sys
sys.modules['sqlite3'] = __import__('pysqlite3')
```

## 验证修复

### 1. 启动应用

```bash
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8010
```

### 2. 检查输出

**修复成功（扩展加载）：**
```
INFO:     Application startup complete.
```

**修复成功（降级模式）：**
```
WARNING:  Failed to load sqlite-vec extension: ...
WARNING:  Failed to create vector table: ...
INFO:     Application startup complete.
```

**如果仍然失败：**
- 检查是否有其他错误信息
- 确认 SQLAlchemy 版本兼容
- 尝试方案 2 或方案 3

### 3. 测试功能

**核心功能测试：**
```bash
# 测试健康检查
curl http://127.0.0.1:8010/api/health

# 应该返回：
{"status":"ok"}
```

**知识库功能测试（如果扩展已加载）：**
1. 登录前端
2. 进入"企业知识库管理"
3. 上传一个文档
4. 生成文案时会使用知识库检索

## 功能降级说明

### 扩展加载成功

```
✅ 文案生成（基础）
✅ 文案生成（知识库增强）← 向量搜索
✅ 知识库上传
✅ 知识库语义检索 ← 向量搜索
✅ 用户认证
✅ 历史记录
```

### 扩展加载失败（降级模式）

```
✅ 文案生成（基础）
⚠️ 文案生成（知识库增强）← 降级为关键词匹配
⚠️ 知识库上传 ← 可上传但无向量索引
⚠️ 知识库检索 ← 降级为全文搜索
✅ 用户认证
✅ 历史记录
```

**影响评估：**
- 如果不使用知识库功能：**无影响**
- 如果使用知识库功能：**检索精度降低，但仍可用**

## 生产环境建议

### 推荐配置

1. **使用支持扩展的 Python 发行版**
   - 官方 Python.org 版本
   - Anaconda/Miniconda
   - Docker 官方 Python 镜像

2. **容器化部署（推荐）**

```dockerfile
FROM python:3.12-slim

# 官方 Python 镜像默认支持扩展
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
WORKDIR /app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8010"]
```

3. **添加环境检查脚本**

```bash
#!/bin/bash
# check_sqlite_extensions.sh

python3 << EOF
import sqlite3
conn = sqlite3.connect(':memory:')
try:
    conn.enable_load_extension(True)
    print("✅ SQLite extensions supported")
    exit(0)
except AttributeError:
    print("⚠️ SQLite extensions NOT supported")
    print("   App will run in degraded mode")
    exit(1)
EOF
```

## 常见问题

### Q1: 修复后仍然报错？

**A:** 确认以下几点：
1. 重启了后端服务
2. 检查 Python 版本 >= 3.10
3. 检查 SQLAlchemy 版本是否兼容
4. 尝试删除 `app.db` 重新初始化

### Q2: 如何知道当前是否加载了扩展？

**A:** 查看启动日志：
- 无警告 = 扩展已加载
- 有警告 = 降级模式

### Q3: 降级模式下知识库还能用吗？

**A:** 可以，但：
- 向量相似度搜索被禁用
- 使用简单的关键词匹配替代
- 检索精度会降低

### Q4: 生产环境必须启用扩展吗？

**A:** 取决于需求：
- 如果依赖知识库检索：**建议启用**
- 如果只用基础文案生成：**可选**

### Q5: 如何完全禁用知识库功能？

**A:** 修改 `backend/app/routers/knowledge.py`：

```python
@router.post("/documents/upload")
async def upload_document(...):
    raise HTTPException(
        status_code=501,
        detail="Knowledge base feature is disabled"
    )
```

## 相关资源

- [sqlite-vec 官方文档](https://github.com/asg017/sqlite-vec)
- [Python SQLite 扩展文档](https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.enable_load_extension)
- [pysqlite3-binary](https://pypi.org/project/pysqlite3-binary/)

## 总结

通过优雅降级策略，应用可以在不支持 SQLite 扩展的环境中正常运行。

**关键要点：**
- ✅ 核心功能不受影响
- ✅ 知识库功能降级但仍可用
- ✅ 生产环境建议使用支持扩展的环境
- ✅ 应用启动更加健壮和容错
