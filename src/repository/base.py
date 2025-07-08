from abc import ABC, abstractmethod
from src.models.memory_point import MemoryPoint

class VectorDBRepository(ABC):
    @abstractmethod
    def upsert(self, point: MemoryPoint):
        pass

    @abstractmethod
    def search(self, query_vector, limit) -> list:
        """MemoryPoint 리스트 반환"""
        pass

    @abstractmethod
    def get_collection_stats(self):
        pass 