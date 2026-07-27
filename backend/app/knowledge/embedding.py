"""Local embedding model wrapper (no external API calls)."""

from pathlib import Path

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

_model = None


def get_local_model_path() -> str | None:
    """
    检查本地 models 目录是否存在预下载的模型

    查找优先级:
    1. {项目根目录}/models/all-MiniLM-L6-v2
    2. 返回 None,使用 HuggingFace 自动下载
    """
    # 获取项目根目录(backend的父目录)
    current_file = Path(__file__)
    backend_dir = current_file.parent.parent.parent  # 从 backend/app/knowledge/ 向上3级
    project_root = backend_dir.parent

    # 本地模型路径
    local_model_path = project_root / "models" / EMBEDDING_MODEL_NAME

    # 检查路径是否存在且包含必要的模型文件
    if local_model_path.exists() and local_model_path.is_dir():
        # 验证关键文件是否存在
        required_files = ["config.json", "pytorch_model.bin"]
        has_required = any((local_model_path / f).exists() for f in required_files)

        # 也支持 safetensors 格式
        has_safetensors = (local_model_path / "model.safetensors").exists()

        if has_required or has_safetensors:
            return str(local_model_path)

    return None


def get_embedding_model():
    """Lazily load and cache the sentence-transformers model as a module-level
    singleton. Called once eagerly at app startup to pre-warm, and reused for
    every subsequent embed call.

    优先从本地 models/ 目录加载,不存在则从 HuggingFace 下载。
    """
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        # 尝试从本地加载
        local_path = get_local_model_path()

        if local_path:
            try:
                print(f"✓ 从本地加载模型: {local_path}")
                _model = SentenceTransformer(local_path)
            except Exception as e:
                # 本地模型文件损坏或不完整(如 safetensors 只拉到了 LFS 指针),
                # 回退到 HuggingFace 直接下载,避免每次启动都因同一个坏文件报错
                print(f"✗ 本地模型加载失败: {e}")
                print(f"  回退到 HuggingFace 下载: {EMBEDDING_MODEL_NAME}")
                _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        else:
            print(f"✓ 本地模型不存在,从 HuggingFace 下载: {EMBEDDING_MODEL_NAME}")
            print(f"  提示: 可运行 python download_model.py 下载到本地以加速启动")
            _model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts, returning normalized 384-dim vectors."""
    if not texts:
        return []
    model = get_embedding_model()
    vectors = model.encode(
        texts,
        batch_size=32,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return [v.tolist() for v in vectors]


def embed_text(text: str) -> list[float]:
    """Embed a single piece of text (e.g. a retrieval query)."""
    return embed_texts([text])[0]
