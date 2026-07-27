from collections.abc import Generator

import sqlite_vec
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@event.listens_for(engine, "connect")
def _load_sqlite_vec_extension(dbapi_conn, connection_record) -> None:
    """加载 sqlite-vec 扩展，如果环境不支持则跳过"""
    try:
        # 检查是否有 enable_load_extension 方法
        if not hasattr(dbapi_conn, "enable_load_extension"):
            import warnings
            warnings.warn(
                "SQLite extension loading not supported in this Python build. "
                "Vector search features will be disabled."
            )
            return

        dbapi_conn.enable_load_extension(True)
        sqlite_vec.load(dbapi_conn)
        dbapi_conn.enable_load_extension(False)
    except AttributeError as e:
        import warnings
        warnings.warn(
            f"Failed to load sqlite-vec extension: {e}. "
            "Vector search features will be disabled."
        )
    except Exception as e:
        import warnings
        warnings.warn(
            f"Unexpected error loading sqlite-vec extension: {e}. "
            "Vector search features will be disabled."
        )


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
