import openai
from typing import List, Optional
from .base import EmbeddingService
from src.utils import ModelEncodeError
from src.config.settings import openai_embedding_config


class OpenAIEmbeddingService(EmbeddingService):

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None, 
                 dimensions: Optional[int] = None, user_identifier: Optional[str] = None):
        # 설정에서 기본값 가져오기
        self.api_key = api_key or openai_embedding_config.openai_api_key
        self.model_name = model_name or openai_embedding_config.openai_model_name
        self.dimensions = dimensions or openai_embedding_config.vector_dimension
        self.user_identifier = user_identifier or openai_embedding_config.user_identifier
        
        # API 키 검증
        if not self.api_key:
            raise ValueError("OpenAI API 키가 설정되지 않았습니다. OPENAI_API_KEY 환경변수를 설정하거나 api_key 매개변수를 제공하세요.")
        
        self.client = openai.OpenAI(api_key=self.api_key)
    
    def encode(self, text: str) -> List[float]:
        try:
            # OpenAI API 파라미터 구성
            params = {
                "input": [text],
                "model": self.model_name
            }
            
            # 차원 지정이 있으면 추가 (text-embedding-3 모델 이상에서 지원)
            if self.dimensions:
                params["dimensions"] = self.dimensions
                
            # 사용자 식별자가 있으면 추가
            if self.user_identifier:
                params["user"] = self.user_identifier
            
            response = self.client.embeddings.create(**params)
            return response.data[0].embedding
        except Exception as e:
            raise ModelEncodeError(f"임베딩 모델 인코딩 실패: {e}")
    
    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        try:
            # OpenAI API 파라미터 구성
            params = {
                "input": texts,
                "model": self.model_name
            }
            
            # 차원 지정이 있으면 추가
            if self.dimensions:
                params["dimensions"] = self.dimensions
                
            # 사용자 식별자가 있으면 추가
            if self.user_identifier:
                params["user"] = self.user_identifier
            
            response = self.client.embeddings.create(**params)
            return [data.embedding for data in response.data]
        except Exception as e:
            raise ModelEncodeError(f"임베딩 모델 인코딩 실패: {e}")
    
    def get_embedding(self, text: str) -> List[float]:
        """단일 텍스트 임베딩 생성 (호환성 메서드)"""
        return self.encode(text) 