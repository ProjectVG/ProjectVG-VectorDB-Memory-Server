from abc import ABC, abstractmethod
from typing import List


class EmbeddingService(ABC):
    """임베딩 서비스 인터페이스 - 다양한 임베딩 모델을 지원하기 위한 추상 클래스."""
    
    @abstractmethod
    def encode(self, text: str) -> List[float]:
        """텍스트를 벡터로 변환 (임베딩)."""
        pass
    
    @abstractmethod
    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """여러 텍스트를 벡터로 변환 (배치 임베딩)."""
        pass 