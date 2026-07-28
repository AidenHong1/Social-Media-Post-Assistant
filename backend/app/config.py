from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


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

    # 图片生成配置 (DALL-E 3 兼容接口)
    image_api_key: str = ""  # 空则复用 llm_api_key
    image_api_base_url: str = "https://api.openai.com/v1"
    image_model: str = "dall-e-3"
    image_storage_dir: str = "storage/images"
    image_generation_enabled: bool = False

    # JWT配置 - 必须通过环境变量设置
    jwt_secret_key: str  # 无默认值，强制从环境变量读取
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    @field_validator('jwt_secret_key')
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError('JWT_SECRET_KEY must be at least 32 characters long')
        if v in ['your-secret-key-change-this-in-production', 'secret', 'change-me']:
            raise ValueError('JWT_SECRET_KEY appears to be a placeholder value. Use a secure random key.')
        return v

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
