from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    app_name: str = "PeopleMind AI"
    app_env: str = "development"
    app_debug: bool = True
    database_url: str = "sqlite:///./peoplemind.db"
    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "qwen3:4b-instruct"
    ollama_embedding_model: str = "embeddinggemma"
    jwt_secret_key: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(
        default=30,
        ge=5,
        le=1440,
    )
    document_upload_dir: str = "data/uploads"
    max_document_size_mb: int = Field(
        default=20,
        ge=1,
        le=100,
    )
    vector_store_dir: str = "data/vector_store"
    vector_collection_name: str = "peoplemind_hr_documents"
    chunk_size: int = Field(
        default=1000,
        ge=300,
        le=4000,
    )
    chunk_overlap: int = Field(
        default=200,
        ge=0,
        le=1000,
    )
    embedding_batch_size: int = Field(
        default=8,
        ge=1,
        le=64,
    )
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8-sig",
        case_sensitive=False,
        extra="ignore",
    )
@lru_cache
def get_settings() -> Settings:
    return Settings()
settings = get_settings()
