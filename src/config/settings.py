import os
from enum import Enum
from pydantic_settings import BaseSettings
from typing import Dict, List, Any

# 임베딩 타입 Enum
class EmbeddingType(str, Enum):
    SENTENCE_TRANSFORMER = "sentence_transformer"
    OPENAI = "openai"

# 메모리 타입 Enum
class MemoryType(str, Enum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"

# 임베딩 타입만
class EmbeddingConfig(BaseSettings):
    embedding_type: EmbeddingType = os.getenv("EMBEDDING_TYPE", "sentence_transformer")

embedding_config = EmbeddingConfig()

# DB 설정
class DBConfig(BaseSettings):
    qdrant_host: str = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port: int = int(os.getenv("QDRANT_PORT", "6333"))
    collection_name: str = os.getenv("QDRANT_COLLECTION", "my_vectors")
    # 벡터 차원 자동 결정
    vector_dim: int = (
        1536 if embedding_config.embedding_type == EmbeddingType.OPENAI else 384
    )

# 서버 설정
class ServerConfig(BaseSettings):
    server_port: int = int(os.getenv("SERVER_PORT", "5602"))
    server_host: str = os.getenv("SERVER_HOST", "0.0.0.0")

# 로깅 설정
class LogConfig(BaseSettings):
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = os.getenv("LOG_FILE", "")

# SentenceTransformer 임베딩 설정
class SentenceTransformerEmbeddingConfig(BaseSettings):
    model_name: str = os.getenv("MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")
    model_cache_dir: str = os.getenv("MODEL_CACHE_DIR", "./model_cache")

# OpenAI 임베딩 설정
class OpenAIEmbeddingConfig(BaseSettings):
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model_name: str = os.getenv("OPENAI_MODEL_NAME", "text-embedding-3-small")

# 컬렉션 설정
class CollectionConfig(BaseSettings):
    collections: Dict[str, Dict[str, Any]] = {
        "episodic": {
            "vector_dim": 1536,
            "distance": "COSINE",
            "metadata_schema": [
                "user_id", "timestamp", "speaker", "emotion", 
                "context", "importance_score", "source", "links"
            ],
            "index_params": {"m": 16, "ef_construct": 200}
        },
        "semantic": {
            "vector_dim": 768,
            "distance": "DOT",
            "metadata_schema": [
                "user_id", "fact_type", "source", "last_updated", 
                "confidence_score", "importance_score"
            ],
            "index_params": {"m": 32, "ef_construct": 400}
        }
    }
    
    default_collection: str = "semantic"
    auto_create_collections: bool = True

# 인스턴스 생성 (통합 진입점)
server_config = ServerConfig()
db_config = DBConfig()
log_config = LogConfig()
sentence_transformer_embedding_config = SentenceTransformerEmbeddingConfig()
openai_embedding_config = OpenAIEmbeddingConfig()
collection_config = CollectionConfig()