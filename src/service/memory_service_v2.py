from typing import List, Dict, Any, Optional
from src.repository.multi_collection_repository import MultiCollectionQdrantRepository
from src.service.intelligent_memory_router import IntelligentMemoryRouter
from src.service.factory import get_embedding_service
from src.config.settings import MemoryType
from src.models.memory_point import MemoryPoint
from datetime import datetime, timezone
import uuid

class MultiCollectionMemoryService:
    """다중 컬렉션 메모리 서비스"""
    
    def __init__(self):
        self.repository = MultiCollectionQdrantRepository()
        self.router = IntelligentMemoryRouter()
        self.embedding_service = get_embedding_service()
    
    def insert_memory_with_auto_classification(
        self, 
        text: str, 
        user_id: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """자동 분류를 통한 메모리 삽입"""
        metadata = metadata or {}
        
        # 메모리 타입 자동 분류
        classification = self.router.classify_with_confidence(text, metadata)
        memory_type = classification["predicted_type"]
        
        # 임베딩 생성
        embedding = self.embedding_service.get_embedding(text)
        
        # 메모리 데이터 구성
        memory_data = {
            "text": text,
            "embedding": embedding,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "importance_score": metadata.get("importance_score", 0.5),
            "source": metadata.get("source", "auto_insert"),
            **metadata  # 추가 메타데이터
        }
        
        # 메모리 삽입
        memory_id = self.repository.insert_memory(memory_data, user_id, memory_type)
        
        return {
            "id": memory_id,
            "memory_type": memory_type,
            "classification": classification,
            "explanation": self.router.get_classification_explanation(text, metadata)
        }
    
    def insert_memory_with_manual_type(
        self,
        text: str,
        user_id: str,
        memory_type: MemoryType,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """수동 지정된 타입으로 메모리 삽입"""
        metadata = metadata or {}
        
        # 임베딩 생성
        embedding = self.embedding_service.get_embedding(text)
        
        # 메모리 데이터 구성
        memory_data = {
            "text": text,
            "embedding": embedding,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "importance_score": metadata.get("importance_score", 0.5),
            "source": metadata.get("source", "manual_insert"),
            **metadata
        }
        
        # 메모리 삽입
        return self.repository.insert_memory(memory_data, user_id, memory_type)
    
    def search_memory_single_collection(
        self,
        query: str,
        user_id: str,
        memory_type: MemoryType,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[MemoryPoint]:
        """단일 컬렉션에서 메모리 검색"""
        # 쿼리 임베딩 생성
        query_vector = self.embedding_service.get_embedding(query)
        
        # 검색 실행
        return self.repository.search_memory(
            query_vector, user_id, memory_type, limit, filters
        )
    
    def search_memory_multi_collection(
        self,
        query: str,
        user_id: str,
        collections: List[MemoryType] = None,
        limit: int = 10,
        weights: Optional[Dict[MemoryType, float]] = None
    ) -> List[MemoryPoint]:
        """다중 컬렉션 통합 검색"""
        if collections is None:
            collections = [MemoryType.EPISODIC, MemoryType.SEMANTIC]
        
        # 쿼리 임베딩 생성
        query_vector = self.embedding_service.get_embedding(query)
        
        # 다중 컬렉션 검색
        return self.repository.multi_collection_search(
            query_vector, user_id, collections, limit, weights
        )
    
    def get_intelligent_search_weights(self, query: str) -> Dict[MemoryType, float]:
        """쿼리 분석을 통한 지능형 가중치 결정"""
        # 쿼리 분류를 통해 가중치 결정
        classification = self.router.classify_with_confidence(query, {})
        
        if classification["predicted_type"] == MemoryType.EPISODIC:
            # Episodic 경향의 쿼리면 Episodic에 높은 가중치
            confidence = classification["confidence"]
            return {
                MemoryType.EPISODIC: 1.0 + confidence * 0.5,
                MemoryType.SEMANTIC: 1.0 - confidence * 0.3
            }
        else:
            # Semantic 경향의 쿼리면 Semantic에 높은 가중치
            confidence = classification["confidence"]
            return {
                MemoryType.EPISODIC: 1.0 - confidence * 0.3,
                MemoryType.SEMANTIC: 1.0 + confidence * 0.5
            }
    
    def search_with_intelligent_weights(
        self,
        query: str,
        user_id: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """지능형 가중치를 사용한 검색"""
        # 자동 가중치 계산
        weights = self.get_intelligent_search_weights(query)
        
        # 검색 실행
        results = self.search_memory_multi_collection(
            query, user_id, [MemoryType.EPISODIC, MemoryType.SEMANTIC], limit, weights
        )
        
        return {
            "results": results,
            "applied_weights": weights,
            "explanation": f"쿼리 '{query}' 분석 결과 적용된 가중치"
        }
    
    def get_user_memory_summary(self, user_id: str) -> Dict[str, Any]:
        """사용자 메모리 요약 정보"""
        episodic_count = self.repository.get_user_memory_count(user_id, MemoryType.EPISODIC)
        semantic_count = self.repository.get_user_memory_count(user_id, MemoryType.SEMANTIC)
        
        return {
            "user_id": user_id,
            "total_memories": episodic_count + semantic_count,
            "episodic_count": episodic_count,
            "semantic_count": semantic_count,
            "memory_distribution": {
                "episodic_ratio": episodic_count / max(episodic_count + semantic_count, 1),
                "semantic_ratio": semantic_count / max(episodic_count + semantic_count, 1)
            }
        }
    
    def classify_existing_memory(self, memory_id: str, text: str) -> Dict[str, Any]:
        """기존 메모리의 분류 재검토"""
        classification = self.router.classify_with_confidence(text, {})
        explanation = self.router.get_classification_explanation(text, {})
        
        return {
            "memory_id": memory_id,
            "current_classification": classification,
            "explanation": explanation,
            "should_reclassify": classification["confidence"] > 0.7
        }
    
    def batch_reclassify_memories(
        self, 
        user_id: str, 
        memory_type: MemoryType,
        confidence_threshold: float = 0.8
    ) -> Dict[str, Any]:
        """배치 재분류 (마이그레이션용)"""
        # TODO: 실제 구현에서는 메모리를 조회하고 재분류하는 로직 필요
        return {
            "user_id": user_id,
            "processed_memories": 0,
            "reclassified_memories": 0,
            "confidence_threshold": confidence_threshold
        }
    
    def delete_user_memories(
        self, 
        user_id: str, 
        memory_type: Optional[MemoryType] = None
    ) -> Dict[str, Any]:
        """사용자 메모리 삭제"""
        try:
            # 삭제 전 카운트 조회
            before_counts = self.get_user_memory_summary(user_id)
            
            # 삭제 실행
            self.repository.delete_user_memories(user_id, memory_type)
            
            # 삭제 후 카운트 조회
            after_counts = self.get_user_memory_summary(user_id)
            
            deleted_count = before_counts["total_memories"] - after_counts["total_memories"]
            
            return {
                "user_id": user_id,
                "deleted_memory_type": memory_type.value if memory_type else "all",
                "deleted_count": deleted_count,
                "remaining_count": after_counts["total_memories"]
            }
            
        except Exception as e:
            return {
                "user_id": user_id,
                "error": str(e),
                "success": False
            }
    
    def reset_collection(self, memory_type: MemoryType) -> Dict[str, Any]:
        """컬렉션 초기화"""
        try:
            collection_name = memory_type.value
            self.repository.reset_collection(collection_name)
            
            return {
                "collection_name": collection_name,
                "memory_type": memory_type.value,
                "reset_success": True,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            return {
                "collection_name": memory_type.value,
                "error": str(e),
                "reset_success": False
            }
    
    def get_collection_stats(self, memory_type: MemoryType) -> Dict[str, Any]:
        """컬렉션 통계 정보"""
        try:
            collection_name = memory_type.value
            stats = self.repository.get_collection_stats(collection_name)
            
            return {
                "collection_name": collection_name,
                "memory_type": memory_type.value,
                "total_points": stats.points_count,
                "vector_size": stats.config.params.vectors.size,
                "distance_function": stats.config.params.vectors.distance.value
            }
            
        except Exception as e:
            return {
                "collection_name": memory_type.value,
                "error": str(e)
            }