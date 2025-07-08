import os
from enum import Enum
from pydantic_settings import BaseSettings


class EmbeddingType(str, Enum):
    """지원하는 임베딩 서비스 타입."""
    SENTENCE_TRANSFORMER = "sentence_transformer"
    OPENAI = "openai"


class Settings(BaseSettings):
    # 서버 설정
    server_port: int = int(os.getenv("SERVER_PORT", "5602"))
    server_host: str = os.getenv("SERVER_HOST", "0.0.0.0")

    # Qdrant 설정
    qdrant_host: str = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port: int = int(os.getenv("QDRANT_PORT", "6333"))
    collection_name: str = "my_vectors"
    
    # 벡터 차원 설정
    vector_dim: int = int(os.getenv("VECTOR_DIM", "384"))
    
    # 임베딩 서비스 설정
    embedding_type: EmbeddingType = os.getenv("EMBEDDING_TYPE", "sentence_transformer")

    # SentenceTransformer 설정
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    model_cache_dir: str = os.getenv("MODEL_CACHE_DIR", "./model_cache")
    
    # OpenAI 설정
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model_name: str = os.getenv("OPENAI_MODEL_NAME", "text-embedding-3-small")

    # 로깅 설정
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = os.getenv("LOG_FILE", "")

settings = Settings() 