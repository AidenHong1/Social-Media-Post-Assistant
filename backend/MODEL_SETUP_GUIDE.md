# Embedding 模型本地化配置指南

## 📋 功能说明

项目现在支持优先从本地 `models/` 目录加载 `all-MiniLM-L6-v2` 模型,避免每次启动时从 HuggingFace 下载。

### 加载优先级

1. **本地路径**: `{项目根目录}/models/all-MiniLM-L6-v2/`
2. **HuggingFace**: 如果本地不存在,自动从 HuggingFace Hub 下载

## 🚀 快速开始

### 方法 1: 使用下载脚本(推荐)

在项目根目录运行:

```bash
python download_model.py
```

该脚本会:
- 创建 `models/` 目录
- 从 HuggingFace 下载 `all-MiniLM-L6-v2`
- 保存到 `models/all-MiniLM-L6-v2/`

### 方法 2: 手动下载

```bash
# 1. 创建目录
mkdir -p models

# 2. 使用 Python 下载
python -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
model.save('models/all-MiniLM-L6-v2')
print('✓ 模型下载完成')
"
```

### 方法 3: 从已有缓存复制

如果你已经在其他项目中使用过此模型,可以从 HuggingFace 缓存目录复制:

```bash
# HuggingFace 缓存位置通常在:
# Linux/Mac: ~/.cache/huggingface/hub/
# Windows: C:\Users\{用户名}\.cache\huggingface\hub\

# 找到类似这样的目录:
# models--sentence-transformers--all-MiniLM-L6-v2

# 复制到项目:
cp -r ~/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/{hash}/* models/all-MiniLM-L6-v2/
```

## 📂 目录结构

完成后的目录结构:

```
Practice/
├── backend/
│   └── app/
│       └── knowledge/
│           └── embedding.py          # 修改后的文件
├── models/                            # 新增目录
│   └── all-MiniLM-L6-v2/             # 本地模型
│       ├── config.json
│       ├── pytorch_model.bin         # 或 model.safetensors
│       ├── tokenizer_config.json
│       ├── vocab.txt
│       └── ...
├── download_model.py                  # 下载脚本
└── ...
```

## ✅ 验证安装

运行应用时检查控制台输出:

### 成功从本地加载:
```
✓ 从本地加载模型: E:\Programming code\Aiden Agent\Practice\models\all-MiniLM-L6-v2
```

### 从 HuggingFace 下载:
```
✓ 本地模型不存在,从 HuggingFace 下载: all-MiniLM-L6-v2
  提示: 可将模型下载到 models/all-MiniLM-L6-v2 目录以加速启动
```

## 🔍 代码变更说明

### 修改的文件
- `backend/app/knowledge/embedding.py`

### 新增功能
1. `get_local_model_path()`: 检测本地模型是否存在
2. 增强的 `get_embedding_model()`: 优先加载本地模型

### 关键逻辑

```python
def get_local_model_path() -> str | None:
    """
    检查本地 models 目录是否存在预下载的模型
    返回本地路径或 None
    """
    # 检查 models/all-MiniLM-L6-v2/ 是否存在
    # 验证必要文件(config.json, pytorch_model.bin 或 model.safetensors)
    # 存在返回路径,不存在返回 None
```

## 📦 模型信息

- **模型名称**: sentence-transformers/all-MiniLM-L6-v2
- **维度**: 384
- **大小**: ~80MB
- **用途**: 文本语义相似度计算,知识库检索

## 🔧 故障排除

### 问题 1: 模型下载失败

**原因**: 网络问题或 HuggingFace 访问受限

**解决方案**:
```bash
# 使用镜像站点(国内)
export HF_ENDPOINT=https://hf-mirror.com
python download_model.py
```

### 问题 2: 模型文件不完整

**症状**: 提示找不到 config.json 或 pytorch_model.bin

**解决方案**:
```bash
# 删除不完整的文件
rm -rf models/all-MiniLM-L6-v2

# 重新下载
python download_model.py
```

### 问题 3: 权限问题

**症状**: Permission denied

**解决方案**:
```bash
# Linux/Mac: 修改权限
chmod -R 755 models/

# Windows: 以管理员身份运行
```

## 🎯 性能提升

使用本地模型的优势:

| 指标 | 首次下载 | 本地加载 |
|------|----------|----------|
| 启动时间 | 30-60秒 | 2-3秒 |
| 网络需求 | ~80MB下载 | 无 |
| 稳定性 | 依赖网络 | 100%稳定 |
| 离线可用 | ❌ | ✅ |

## 📚 相关资源

- [Sentence Transformers 文档](https://www.sbert.net/)
- [all-MiniLM-L6-v2 模型卡片](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
- [HuggingFace Hub 文档](https://huggingface.co/docs/hub/index)

## ⚠️ 注意事项

1. **模型文件较大**: 确保有足够的磁盘空间(至少 200MB)
2. **首次下载**: 首次使用仍需联网下载,之后可离线使用
3. **版本管理**: models/ 目录建议加入 .gitignore
4. **更新模型**: 如需更新模型,删除本地目录后重新下载

## 🔐 .gitignore 配置

建议在 `.gitignore` 中添加:

```gitignore
# 模型文件
models/
*.bin
*.safetensors
```

---

**更新日期**: 2026-07-27  
**版本**: v1.0
