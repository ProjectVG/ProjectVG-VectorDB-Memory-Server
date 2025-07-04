from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from src.config import settings

class VectorDBRepository:
    """Qdrant 벡터 데이터베이스와의 데이터 접근 (CRUD)"""
    def __init__(self):
        """Qdrant 클라이언트 및 컬렉션 초기화."""
        self.qdrant = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
        self.collection_name = settings.collection_name
        self._ensure_collection()

    def _ensure_collection(self):
        if self.collection_name not in self.qdrant.get_collections().collections:
            self.qdrant.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )

    def upsert(self, point: PointStruct):
        """포인트(벡터)를 컬렉션에 삽입 또는 업데이트."""
        self.qdrant.upsert(collection_name=self.collection_name, points=[point])

    def search(self, query_vector, limit):
        """쿼리 벡터로 유사도 검색."""
        return self.qdrant.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit
        )

    def get_collection_stats(self):
        """컬렉션 통계 정보 반환."""
        return self.qdrant.get_collection(self.collection_name) 
