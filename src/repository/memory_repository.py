from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from src.config.settings import db_config, collection_config, MemoryType
from src.repository.base import VectorDBRepository
from src.models.memory_point import MemoryPoint
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import math

class MemoryQdrantRepository(VectorDBRepository):
    """다중 컬렉션 지원 Qdrant 벡터 데이터베이스 Repository"""
    
    def __init__(self):
        self.qdrant = QdrantClient(host=db_config.qdrant_host, port=db_config.qdrant_port)
        self.collection_configs = collection_config.collections
        
    def _ensure_collection(self, collection_name: str):
        """컬렉션이 존재하지 않으면 생성"""
        collections = [c.name for c in self.qdrant.get_collections().collections]
        
        if collection_name not in collections:
            if collection_name not in self.collection_configs:
                raise ValueError(f"Unknown collection type: {collection_name}")
                
            config = self.collection_configs[collection_name]
            distance_map = {
                "COSINE": Distance.COSINE,
                "DOT": Distance.DOT,
                "EUCLIDEAN": Distance.EUCLID
            }
            
            self.qdrant.recreate_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=config["vector_dim"], 
                    distance=distance_map.get(config["distance"], Distance.COSINE)
                )
            )

    def get_collection_by_type(self, memory_type: MemoryType) -> str:
        """메모리 타입에 따른 컬렉션 이름 반환"""
        return memory_type.value

    def insert_memory(self, memory_data: dict, user_id: str, memory_type: MemoryType) -> str:
        """user_id를 메타데이터로 추가하여 저장"""
        collection_name = self.get_collection_by_type(memory_type)
        self._ensure_collection(collection_name)
        
        # user_id를 메타데이터에 추가
        memory_data["user_id"] = user_id
        
        point_id = str(uuid.uuid4())
        qdrant_point = PointStruct(
            id=point_id,
            vector=memory_data.get("embedding") or memory_data.get("vector"),
            payload=memory_data
        )
        
        self.qdrant.upsert(collection_name=collection_name, points=[qdrant_point])
        return point_id
        
    def search_memory(self, query_vector: List[float], user_id: str, memory_type: MemoryType, limit: int = 10, filters: Optional[Dict] = None) -> List[MemoryPoint]:
        """user_id 필터링으로 사용자별 검색"""
        collection_name = self.get_collection_by_type(memory_type)
        self._ensure_collection(collection_name)
        
        # user_id 필터 조건
        filter_conditions = [
            FieldCondition(key="user_id", match=MatchValue(value=user_id))
        ]
        
        # 추가 필터가 있으면 포함
        if filters:
            for key, value in filters.items():
                filter_conditions.append(
                    FieldCondition(key=key, match=MatchValue(value=value))
                )
        
        results = self.qdrant.search(
            collection_name=collection_name,
            query_vector=query_vector,
            query_filter=Filter(must=filter_conditions) if filter_conditions else None,
            limit=limit
        )
        
        memory_points = []
        for result in results:
            memory_point = MemoryPoint(vector=result.vector, metadata=result.payload)
            memory_point.score = result.score
            memory_point.id = result.id
            memory_points.append(memory_point)
            
        return memory_points

    def multi_collection_search(self, query_vector: List[float], user_id: str, collections: List[MemoryType], limit: int = 10, weights: Optional[Dict[MemoryType, float]] = None) -> List[MemoryPoint]:
        """다중 컬렉션 검색"""
        all_results = []
        
        for memory_type in collections:
            results = self.search_memory(query_vector, user_id, memory_type, limit)
            
            # 가중치 적용
            weight = weights.get(memory_type, 1.0) if weights else 1.0
            for result in results:
                result.score = result.score * weight
                result.collection_type = memory_type.value
                all_results.append(result)
        
        # 점수순으로 정렬하고 limit 적용
        all_results.sort(key=lambda x: x.score, reverse=True)
        return all_results[:limit]

    def upsert(self, point: MemoryPoint, collection_name=None):
        """기존 인터페이스 호환성을 위한 메서드"""
        collection_name = collection_name or db_config.collection_name
        self._ensure_collection(collection_name)
        qdrant_point = PointStruct(
            id=str(uuid.uuid4()),
            vector=point.vector,
            payload=point.metadata
        )
        self.qdrant.upsert(collection_name=collection_name, points=[qdrant_point])

    def search(self, query_vector, limit, collection_name=None) -> list:
        """기존 인터페이스 호환성을 위한 메서드"""
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
        """컬렉션 통계 정보 반환"""
        collection_name = collection_name or db_config.collection_name
        self._ensure_collection(collection_name)
        return self.qdrant.get_collection(collection_name)

    def reset_collection(self, collection_name=None, vector_dim=None):
        """컬렉션 초기화"""
        collection_name = collection_name or db_config.collection_name
        collections = [c.name for c in self.qdrant.get_collections().collections]
        
        if collection_name in collections:
            self.qdrant.delete_collection(collection_name=collection_name)
            
        # 컬렉션 재생성
        if collection_name in self.collection_configs:
            config = self.collection_configs[collection_name]
            distance_map = {
                "COSINE": Distance.COSINE,
                "DOT": Distance.DOT,
                "EUCLIDEAN": Distance.EUCLID
            }
            
            self.qdrant.recreate_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=config["vector_dim"],
                    distance=distance_map.get(config["distance"], Distance.COSINE)
                )
            )
        else:
            # 기본 설정으로 생성
            self.qdrant.recreate_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_dim or db_config.vector_dim, distance=Distance.COSINE)
            )

    def get_user_memory_count(self, user_id: str, memory_type: MemoryType) -> int:
        """사용자별 메모리 개수 조회"""
        collection_name = self.get_collection_by_type(memory_type)
        self._ensure_collection(collection_name)
        
        result = self.qdrant.count(
            collection_name=collection_name,
            count_filter=Filter(
                must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]
            )
        )
        return result.count

    def delete_user_memories(self, user_id: str, memory_type: Optional[MemoryType] = None):
        """사용자의 메모리 삭제"""
        collections_to_delete = [memory_type] if memory_type else list(MemoryType)
        
        for mem_type in collections_to_delete:
            collection_name = self.get_collection_by_type(mem_type)
            self._ensure_collection(collection_name)
            
            self.qdrant.delete(
                collection_name=collection_name,
                points_selector=Filter(
                    must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]
                )
            )

    def batch_insert_memories(self, memories: List[Dict], user_id: str, memory_type: MemoryType) -> List[str]:
        """배치로 다중 메모리 삽입"""
        collection_name = self.get_collection_by_type(memory_type)
        self._ensure_collection(collection_name)
        
        points = []
        memory_ids = []
        
        for memory_data in memories:
            memory_data["user_id"] = user_id
            memory_id = str(uuid.uuid4())
            memory_ids.append(memory_id)
            
            qdrant_point = PointStruct(
                id=memory_id,
                vector=memory_data.get("embedding") or memory_data.get("vector"),
                payload=memory_data
            )
            points.append(qdrant_point)
        
        # 배치 삽입 실행
        self.qdrant.upsert(collection_name=collection_name, points=points)
        return memory_ids

    def search_memory_with_time_weight(self, query_vector: List[float], user_id: str, memory_type: MemoryType, 
                                      limit: int = 10, filters: Optional[Dict] = None, 
                                      time_weight: float = 0.3, decay_days: int = 30) -> List[MemoryPoint]:
        """시간 가중치가 적용된 메모리 검색 (최근 기억일수록 높은 점수)"""
        collection_name = self.get_collection_by_type(memory_type)
        self._ensure_collection(collection_name)
        
        # user_id 필터 조건
        filter_conditions = [
            FieldCondition(key="user_id", match=MatchValue(value=user_id))
        ]
        
        # 추가 필터가 있으면 포함
        if filters:
            for key, value in filters.items():
                filter_conditions.append(
                    FieldCondition(key=key, match=MatchValue(value=value))
                )
        
        # 더 많은 결과를 가져와서 시간 가중치 적용 후 재정렬
        search_limit = min(limit * 3, 100)  # 3배수만큼 가져와서 시간 가중치 적용
        
        results = self.qdrant.search(
            collection_name=collection_name,
            query_vector=query_vector,
            query_filter=Filter(must=filter_conditions) if filter_conditions else None,
            limit=search_limit
        )
        
        # 시간 가중치 적용
        current_time = datetime.now(timezone.utc)
        memory_points = []
        
        for result in results:
            timestamp_str = result.payload.get("timestamp")
            if timestamp_str:
                try:
                    memory_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    days_ago = (current_time - memory_time).days
                    
                    # 지수 감쇠 함수: exp(-days_ago / decay_days)
                    time_decay = math.exp(-days_ago / decay_days)
                    
                    # 원본 유사도 점수와 시간 가중치 결합
                    adjusted_score = result.score * (1 - time_weight) + time_decay * time_weight
                    
                except (ValueError, TypeError):
                    # 시간 파싱 실패 시 원본 점수 사용
                    adjusted_score = result.score
            else:
                # 타임스탬프 없으면 원본 점수 사용
                adjusted_score = result.score
            
            memory_point = MemoryPoint(vector=result.vector, metadata=result.payload)
            memory_point.score = adjusted_score
            memory_point.id = result.id
            memory_points.append(memory_point)
        
        # 조정된 점수로 재정렬하고 limit 적용
        memory_points.sort(key=lambda x: x.score, reverse=True)
        return memory_points[:limit]