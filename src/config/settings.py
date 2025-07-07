import os
from enum import Enum
from pydantic_settings import BaseSettings


class EmbeddingType(str, Enum):
    """지원하는 임베딩 서비스 타입."""
    SENTENCE_TRANSFORMER = "sentence_transformer"
    OPENAI = "openai"


class Settings(BaseSettings):
    # Qdrant 설정
    qdrant_host: str = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port: int = int(os.getenv("QDRANT_PORT", "6333"))
    collection_name: str = "my_vectors"
    
    # 임베딩 서비스 설정
    embedding_type: EmbeddingType = os.getenv("EMBEDDING_TYPE", "sentence_transformer")
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # OpenAI 설정 (향후 사용)
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model_name: str = os.getenv("OPENAI_MODEL_NAME", "text-embedding-ada-002")

settings = Settings() 