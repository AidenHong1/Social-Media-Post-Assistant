#!/usr/bin/env python3
"""
下载 all-MiniLM-L6-v2 模型到本地 models 目录

使用方法:
    python download_model.py

这将把模型下载到 models/all-MiniLM-L6-v2 目录下
"""

import sys
from pathlib import Path


def download_model():
    """下载 sentence-transformers 模型到本地目录"""

    # 设置本地模型保存路径
    project_root = Path(__file__).parent
    models_dir = project_root / "models"
    model_name = "all-MiniLM-L6-v2"
    local_model_path = models_dir / model_name

    print("=" * 60)
    print("下载 Sentence Transformers 模型到本地")
    print("=" * 60)
    print(f"模型名称: {model_name}")
    print(f"保存路径: {local_model_path}")
    print()

    # 创建 models 目录
    models_dir.mkdir(exist_ok=True)
    print(f"✓ 创建目录: {models_dir}")

    # 检查是否已存在
    if local_model_path.exists():
        print(f"✓ 模型已存在: {local_model_path}")
        user_input = input("是否重新下载? (y/N): ").strip().lower()
        if user_input != 'y':
            print("取消下载")
            return

    # 下载模型
    try:
        print(f"\n开始下载模型...")
        print("(首次下载可能需要几分钟,取决于网络速度)")
        print()

        from sentence_transformers import SentenceTransformer

        # 从 HuggingFace 下载并保存到本地
        model = SentenceTransformer(model_name)
        model.save(str(local_model_path))

        print()
        print("=" * 60)
        print("✓ 模型下载成功!")
        print("=" * 60)
        print(f"保存位置: {local_model_path}")
        print()
        print("现在启动应用时将自动使用本地模型,无需再次下载。")

    except ImportError:
        print("✗ 错误: 未安装 sentence-transformers")
        print("请先安装: pip install sentence-transformers")
        sys.exit(1)
    except Exception as e:
        print(f"✗ 下载失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    download_model()
