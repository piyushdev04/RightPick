from functools import lru_cache
from typing import List

from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Hunnit Product Assistant"

    database_url: str

    # Vector / embeddings
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chroma_db_dir: str = "./chroma_db"

    # OpenAI 
    openai_api_key: str | None = None

    # CORS
    backend_cors_origins: List[str] = []

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()


