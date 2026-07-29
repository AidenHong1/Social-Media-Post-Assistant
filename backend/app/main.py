from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import pysqlite3
sys.modules["sqlite3"] = pysqlite3
from sqlalchemy import text

from app.config import settings
from app.db import Base, engine
from app.knowledge.embedding import get_embedding_model
from app.routers import auth, generate, history, images, knowledge, templates, variants

app = FastAPI(title="AI Social Post Generator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)

    # 执行数据库迁移
    from pathlib import Path
    migration_file = Path(__file__).parent.parent / "migrations" / "001_add_variant_images.sql"
    if migration_file.exists():
        try:
            with engine.begin() as conn:
                # 检查 variant_images 表是否已存在
                result = conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table' AND name='variant_images'")
                )
                if not result.fetchone():
                    # 执行迁移
                    migration_sql = migration_file.read_text(encoding='utf-8')
                    for statement in migration_sql.split(';'):
                        statement = statement.strip()
                        if statement:
                            conn.execute(text(statement))
                    import warnings
                    warnings.warn("Successfully migrated: added variant_images table")
        except Exception as e:
            import warnings
            warnings.warn(f"Migration warning: {e}")

    # 尝试创建向量表，如果扩展未加载则跳过
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "CREATE VIRTUAL TABLE IF NOT EXISTS vec_chunks USING vec0("
                    "chunk_id INTEGER PRIMARY KEY, embedding FLOAT[384])"
                )
            )
    except Exception as e:
        import warnings
        warnings.warn(
            f"Failed to create vector table: {e}. "
            "Vector search features will be disabled. "
            "The app will continue to work without knowledge base retrieval."
        )

    # 加载嵌入模型
    try:
        get_embedding_model()
    except Exception as e:
        import warnings
        warnings.warn(f"Failed to load embedding model: {e}")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth.router, prefix="/api")
app.include_router(generate.router, prefix="/api")
app.include_router(history.router, prefix="/api")
app.include_router(variants.router, prefix="/api")
app.include_router(knowledge.router, prefix="/api")
app.include_router(templates.router, prefix="/api")
app.include_router(images.router, prefix="/api")
