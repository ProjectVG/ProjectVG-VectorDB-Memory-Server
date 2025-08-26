import openai
from typing import List
from .base import EmbeddingService
from src.utils import ModelEncodeError


class OpenAIEmbeddingService(EmbeddingService):

    def __init__(self, api_key: str, model_name: str = "text-embedding-3-small", 
                 dimensions: int = None, user_identifier: str = None):
        self.api_key = api_key
        self.model_name = model_name
        self.dimensions = dimensions
        self.user_identifier = user_identifier
        self.client = openai.OpenAI(api_key=api_key)
    
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