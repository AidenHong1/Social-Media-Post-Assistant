from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.8
    llm_request_timeout: float = 60.0

    database_url: str = "sqlite:///./app.db"
    cors_origins: list[str] = ["http://localhost:5173"]

    max_upload_mb: int = 10
    knowledge_storage_dir: str = "storage/knowledge_uploads"

    # JWT配置
    jwt_secret_key: str = "your-secret-key-change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
