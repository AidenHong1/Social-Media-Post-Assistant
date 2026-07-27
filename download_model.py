#!/usr/bin/env python3
"""
下载 all-MiniLM-L6-v2 模型到本地 models 目录

使用方法:
    python download_model.py

这将把模型下载到 models/all-MiniLM-L6-v2 目录下
"""

import sys
import shutil
from pathlib import Path


def verify_model(model_path: Path) -> bool:
    """验证模型文件是否完整"""
    # 检查必需文件
    required_files = ["config.json"]
    for f in required_files:
        if not (model_path / f).exists():
            return False

    # 检查权重文件(至少有一个)
    weight_files = [
        model_path / "pytorch_model.bin",
        model_path / "model.safetensors",
    ]
    has_weights = any(f.exists() and f.stat().st_size > 1000 for f in weight_files)

    if not has_weights:
        return False

    # 尝试加载模型验证完整性
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(str(model_path))
        # 测试编码功能
        model.encode(["test"], show_progress_bar=False)
        return True
    except Exception as e:
        print(f"模型验证失败: {e}")
        return False


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
        print(f"\n检测到已存在的模型目录: {local_model_path}")
        print("正在验证模型完整性...")

        if verify_model(local_model_path):
            print("✓ 模型验证通过,无需重新下载")
            return
        else:
            print("✗ 模型文件损坏或不完整")
            user_input = input("是否删除并重新下载? (Y/n): ").strip().lower()
            if user_input not in ['', 'y', 'yes']:
                print("取消操作")
                return

            print(f"删除损坏的模型目录: {local_model_path}")
            shutil.rmtree(local_model_path)

    # 下载模型
    try:
        print(f"\n开始下载模型...")
        print("(首次下载可能需要几分钟,取决于网络速度)")
        print()

        from sentence_transformers import SentenceTransformer

        # 从 HuggingFace 下载
        # 注意: 这会先下载到 HuggingFace 缓存,然后我们保存一份到本地
        print("从 HuggingFace Hub 下载...")
        model = SentenceTransformer(model_name)

        print(f"保存到本地目录: {local_model_path}")
        model.save(str(local_model_path))

        # 验证下载的模型
        print("\n验证下载的模型...")
        if not verify_model(local_model_path):
            print("✗ 警告: 模型下载后验证失败,可能不完整")
            sys.exit(1)

        print()
        print("=" * 60)
        print("✓ 模型下载并验证成功!")
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
        print("\n可能的解决方案:")
        print("1. 检查网络连接")
        print("2. 如果在国内,设置镜像: export HF_ENDPOINT=https://hf-mirror.com")
        print("3. 确保有足够的磁盘空间(至少 200MB)")
        sys.exit(1)


if __name__ == "__main__":
    download_model()
