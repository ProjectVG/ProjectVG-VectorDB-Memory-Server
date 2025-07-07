from typing import List
from sentence_transformers import SentenceTransformer
from src.utils import ModelEncodeError
from .base import EmbeddingService


class SentenceTransformerEmbeddingService(EmbeddingService):
    """SentenceTransformer를 사용하는 임베딩 서비스 구현체."""
    
    def __init__(self, model: SentenceTransformer):
        """SentenceTransformer 모델을 주입받아 초기화."""
        self.model = model
    
    def encode(self, text: str) -> List[float]:
        """단일 텍스트를 벡터로 변환."""
        try:
            return self.model.encode(text).tolist()
        except Exception as e:
            raise ModelEncodeError(f"임베딩 모델 인코딩 실패: {e}")
    
    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """여러 텍스트를 벡터로 변환 (배치 처리)."""
        try:
            return self.model.encode(texts).tolist()
        except Exception as e:
            raise ModelEncodeError(f"임베딩 모델 배치 인코딩 실패: {e}") 