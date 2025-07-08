from sentence_transformers import SentenceTransformer
from src.repository.base import VectorDBRepository
from src.repository.vector_db_repository import QdrantVectorDBRepository
from src.service.memory_service import MemoryService
from src.service.embedding import (
    EmbeddingService,
    SentenceTransformerEmbeddingService,
    OpenAIEmbeddingService
)
from src.config.settings import (
    EmbeddingType, embedding_config, sentence_transformer_embedding_config, openai_embedding_config
)

_model = None
_embedding_service = None
_service = None

import logging

logger = logging.getLogger(__name__)

def get_model():
    """SentenceTransformer 모델 싱글톤 인스턴스 반환."""
    global _model
    if _model is None:
        logger.info(f"모델 로딩 중: {sentence_transformer_embedding_config.model_name}")
        logger.info(f"캐시 디렉토리: {sentence_transformer_embedding_config.model_cache_dir}")
        
        _model = SentenceTransformer(sentence_transformer_embedding_config.model_name)
        logger.info("모델 로딩 완료")
    return _model

def create_embedding_service() -> EmbeddingService:
    """설정에 따라 적절한 임베딩 서비스 인스턴스를 생성."""
    if embedding_config.embedding_type == EmbeddingType.SENTENCE_TRANSFORMER:
        model = get_model()
        return SentenceTransformerEmbeddingService(model)
    
    elif embedding_config.embedding_type == EmbeddingType.OPENAI:
        if not openai_embedding_config.openai_api_key:
            raise ValueError("OpenAI API 키가 설정되지 않았습니다. OPENAI_API_KEY 환경변수를 설정해주세요.")
        return OpenAIEmbeddingService(
            api_key=openai_embedding_config.openai_api_key,
            model_name=openai_embedding_config.openai_model_name
        )
    
    else:
        raise ValueError(f"지원하지 않는 임베딩 타입입니다: {embedding_config.embedding_type}")

def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = create_embedding_service()
    return _embedding_service

def get_memory_service():
    global _service
    if _service is None:
        repo = QdrantVectorDBRepository()
        embedding_service = get_embedding_service()
        _service = MemoryService(embedding_service, repo)
    return _service 