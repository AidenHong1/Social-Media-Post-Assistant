from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.db import Base, engine
from app.knowledge.embedding import get_embedding_model
from app.routers import generate, history, knowledge, variants

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
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE VIRTUAL TABLE IF NOT EXISTS vec_chunks USING vec0("
                "chunk_id INTEGER PRIMARY KEY, embedding FLOAT[384])"
            )
        )
    get_embedding_model()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(generate.router, prefix="/api")
app.include_router(history.router, prefix="/api")
app.include_router(variants.router, prefix="/api")
app.include_router(knowledge.router, prefix="/api")
