from typing import List
from .base import EmbeddingService


class OpenAIEmbeddingService(EmbeddingService):
    """OpenAI API를 사용하는 임베딩 서비스 구현체 (향후 구현 예정)."""
    
    def __init__(self, api_key: str, model_name: str = "text-embedding-ada-002"):
        """OpenAI API 키와 모델명을 주입받아 초기화."""
        self.api_key = api_key
        self.model_name = model_name
        # TODO: OpenAI 클라이언트 초기화
        # self.client = openai.OpenAI(api_key=api_key)
    
    def encode(self, text: str) -> List[float]:
        """OpenAI API를 사용하여 단일 텍스트를 벡터로 변환."""
        # TODO: OpenAI API 호출 구현
        # response = self.client.embeddings.create(
        #     input=text,
        #     model=self.model_name
        # )
        # return response.data[0].embedding
        raise NotImplementedError("OpenAI 임베딩 서비스는 아직 구현되지 않았습니다.")
    
    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """OpenAI API를 사용하여 여러 텍스트를 벡터로 변환."""
        # TODO: OpenAI API 배치 호출 구현
        # response = self.client.embeddings.create(
        #     input=texts,
        #     model=self.model_name
        # )
        # return [data.embedding for data in response.data]
        raise NotImplementedError("OpenAI 임베딩 서비스는 아직 구현되지 않았습니다.") 