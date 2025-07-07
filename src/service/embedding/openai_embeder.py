import openai
from typing import List
from .base import EmbeddingService
from src.utils import ModelEncodeError


class OpenAIEmbeddingService(EmbeddingService):

    def __init__(self, api_key: str, model_name: str = "text-embedding-3-small"):
        self.api_key = api_key
        self.model_name = model_name
        self.client = openai.OpenAI(api_key=api_key)
    
    def encode(self, text: str) -> List[float]:
        try:
            response = self.client.embeddings.create(
                input=[text],
                model=self.model_name
            )
            return response.data[0].embedding
        except Exception as e:
            raise ModelEncodeError(f"임베딩 모델 인코딩 실패: {e}")
    
    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        try:
            response = self.client.embeddings.create(
                input=texts,
                model=self.model_name
            )
            return [data.embedding for data in response.data]
        except Exception as e:
            raise ModelEncodeError(f"임베딩 모델 인코딩 실패: {e}") 