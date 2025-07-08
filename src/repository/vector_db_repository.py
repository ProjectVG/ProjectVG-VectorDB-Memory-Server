from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from src.config.settings import db_config
from src.repository.base import VectorDBRepository
from src.models.memory_point import MemoryPoint
import uuid

class QdrantVectorDBRepository(VectorDBRepository):
    """Qdrant 벡터 데이터베이스와의 데이터 접근 (CRUD)"""
    def __init__(self):
        """Qdrant 클라이언트 및 컬렉션 초기화."""
        self.qdrant = QdrantClient(host=db_config.qdrant_host, port=db_config.qdrant_port)
        self.collection_name = db_config.collection_name
        self._ensure_collection()

    def _ensure_collection(self):
        if self.collection_name not in self.qdrant.get_collections().collections:
            self.qdrant.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=db_config.vector_dim, distance=Distance.COSINE)
            )

    def upsert(self, point: MemoryPoint):
        qdrant_point = PointStruct(
            id=str(uuid.uuid4()),
            vector=point.vector,
            payload=point.metadata
        )
        self.qdrant.upsert(collection_name=self.collection_name, points=[qdrant_point])

    def search(self, query_vector, limit) -> list:
        results = self.qdrant.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit
        )
        memory_points = [MemoryPoint(vector=result.vector, metadata=result.payload) for result in results]
        return memory_points

    def get_collection_stats(self):
        return self.qdrant.get_collection(self.collection_name) 
