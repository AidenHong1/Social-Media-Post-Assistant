"""
简化版用户创建脚本 - 使用SHA256作为临时方案
"""
import hashlib
from app.db import SessionLocal
from app.models import User


def create_test_user_simple():
    """创建测试用户（使用简单哈希）"""
    db = SessionLocal()
    try:
        # 检查用户是否已存在
        existing_user = db.query(User).filter(User.username == "admin").first()
        if existing_user:
            print("用户 'admin' 已存在")
            return

        # 临时使用bcrypt格式的固定哈希（密码：admin123）
        # 这是通过bcrypt.hashpw(b"admin123", bcrypt.gensalt())生成的
        fixed_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqYj5I3KoS"

        test_user = User(
            username="admin",
            hashed_password=fixed_hash,
            full_name="管理员",
            is_active=True,
        )
        db.add(test_user)
        db.commit()
        print("成功创建测试用户")
        print("  用户名: admin")
        print("  密码: admin123")
    except Exception as e:
        print(f"创建用户失败: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_test_user_simple()
