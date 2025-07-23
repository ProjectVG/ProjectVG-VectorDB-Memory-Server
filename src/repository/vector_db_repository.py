from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from src.config.settings import db_config
from src.repository.base import VectorDBRepository
from src.models.memory_point import MemoryPoint
import uuid

class QdrantVectorDBRepository(VectorDBRepository):
    """Qdrant 벡터 데이터베이스와의 데이터 접근 (CRUD)"""
    def __init__(self):
        self.qdrant = QdrantClient(host=db_config.qdrant_host, port=db_config.qdrant_port)

    def _ensure_collection(self, collection_name, vector_dim=None):
        if collection_name not in self.qdrant.get_collections().collections:
            self.qdrant.recreate_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_dim or db_config.vector_dim, distance=Distance.COSINE)
            )

    def upsert(self, point: MemoryPoint, collection_name=None):
        collection_name = collection_name or db_config.collection_name
        self._ensure_collection(collection_name)
        qdrant_point = PointStruct(
            id=str(uuid.uuid4()),
            vector=point.vector,
            payload=point.metadata
        )
        self.qdrant.upsert(collection_name=collection_name, points=[qdrant_point])

    def search(self, query_vector, limit, collection_name=None) -> list:
        collection_name = collection_name or db_config.collection_name
        self._ensure_collection(collection_name)
        results = self.qdrant.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit
        )
        memory_points = [MemoryPoint(vector=result.vector, metadata=result.payload) for result in results]
        return memory_points

    def get_collection_stats(self, collection_name=None):
        collection_name = collection_name or db_config.collection_name
        self._ensure_collection(collection_name)
        return self.qdrant.get_collection(collection_name)

    def reset_collection(self, collection_name=None, vector_dim=None):
        collection_name = collection_name or db_config.collection_name
        if collection_name in self.qdrant.get_collections().collections:
            self.qdrant.delete_collection(collection_name=collection_name)
        self.qdrant.recreate_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_dim or db_config.vector_dim, distance=Distance.COSINE)
        ) 
