from typing import List
from sentence_transformers import SentenceTransformer
from src.utils import ModelEncodeError
from .base import EmbeddingService


class SentenceTransformerEmbeddingService(EmbeddingService):

    def __init__(self, model: SentenceTransformer):
        self.model = model
    
    def encode(self, text: str) -> List[float]:
        try:
            return self.model.encode(text).tolist()
        except Exception as e:
            raise ModelEncodeError(f"임베딩 모델 인코딩 실패: {e}")
    
    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        try:
            return self.model.encode(texts).tolist()
        except Exception as e:
            raise ModelEncodeError(f"임베딩 모델 배치 인코딩 실패: {e}") 