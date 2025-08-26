"""
메모리 파사드 서비스
- Facade 패턴: 복잡한 서비스들을 단일 인터페이스로 제공
- 서비스 간 조율 및 통합 로직 담당
"""
from typing import List, Dict, Any, Optional
from src.config.settings import MemoryType
from src.models.memory_point import MemoryPoint
from src.service.classification_service import MemoryClassificationService
from src.service.search_service import MemorySearchService, IntelligentSearchService
from src.repository.memory_repository import MemoryQdrantRepository
from src.infra.embedding import OpenAIEmbeddingService
from datetime import datetime, timezone


class MemoryFacadeService:
    """메모리 시스템의 통합 파사드"""
    
    def __init__(self):
        # 각 서비스 의존성 주입 (DI 패턴)
        self.classification_service = MemoryClassificationService()
        self.search_service = MemorySearchService()
        self.intelligent_search_service = IntelligentSearchService()
        self.repository = MemoryQdrantRepository()
        self.embedding_service = OpenAIEmbeddingService()
    
    # === 메모리 삽입 관련 메서드 ===
    
    def insert_memory_with_auto_classification(
        self, 
        text: str, 
        user_id: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """자동 분류를 통한 메모리 삽입"""
        metadata = metadata or {}
        
        # 1. 메모리 분류
        classification_result = self.classification_service.classify_memory(text, metadata)
        memory_type = classification_result["predicted_type"]
        
        # 2. 임베딩 생성
        embedding = self.embedding_service.get_embedding(text)
        
        # 3. 메모리 데이터 구성
        memory_data = self._build_memory_data(text, embedding, metadata)
        
        # 4. 메모리 삽입
        memory_id = self.repository.insert_memory(memory_data, user_id, memory_type)
        
        # 5. 결과 반환
        return {
            "id": memory_id,
            "memory_type": memory_type.value,
            "classification": classification_result,
            "confidence": classification_result["confidence"],
            "explanation": classification_result["explanation"]
        }
    
    def insert_memory_with_manual_type(
        self,
        text: str,
        user_id: str,
        memory_type: MemoryType,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """수동 지정된 타입으로 메모리 삽입"""
        metadata = metadata or {}
        
        # 임베딩 생성
        embedding = self.embedding_service.get_embedding(text)
        
        # 메모리 데이터 구성
        memory_data = self._build_memory_data(text, embedding, metadata)
        
        # 메모리 삽입
        memory_id = self.repository.insert_memory(memory_data, user_id, memory_type)
        
        return {
            "id": memory_id,
            "memory_type": memory_type.value,
            "classification_method": "manual",
            "text": text
        }
    
    # === 메모리 검색 관련 메서드 ===
    
    def search_memory_intelligent(
        self,
        query: str,
        user_id: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """지능형 검색 (쿼리 분석 기반)"""
        return self.intelligent_search_service.intelligent_search(query, user_id, limit)
    
    def search_memory_single_collection(
        self,
        query: str,
        user_id: str,
        memory_type: MemoryType,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[MemoryPoint]:
        """단일 컬렉션 검색"""
        return self.search_service.search_single_collection(
            query, user_id, memory_type, limit, filters
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
        return self.search_service.search_multi_collection(
            query, user_id, collections, limit, weights
        )
    
    def search_with_intelligent_weights(
        self,
        query: str,
        user_id: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """지능형 가중치를 사용한 검색 (하위 호환성)"""
        # 쿼리 분류를 통한 가중치 결정
        classification = self.classification_service.classify_memory(query, {})
        weights = self._calculate_search_weights(classification)
        
        # 검색 실행
        results = self.search_service.search_multi_collection(
            query, user_id, [MemoryType.EPISODIC, MemoryType.SEMANTIC], limit, weights
        )
        
        return {
            "results": results,
            "applied_weights": weights,
            "query_classification": classification,
            "explanation": f"쿼리 '{query}' 분석 결과 적용된 가중치"
        }
    
    def search_time_weighted(
        self,
        query: str,
        user_id: str,
        memory_type: MemoryType = MemoryType.EPISODIC,
        limit: int = 10,
        decay_factor: float = 0.1
    ) -> List[MemoryPoint]:
        """시간 가중치 검색"""
        return self.search_service.time_weighted_search(
            query, user_id, memory_type, limit, decay_factor
        )
    
    # === 메모리 관리 관련 메서드 ===
    
    def get_user_memory_summary(self, user_id: str) -> Dict[str, Any]:
        """사용자 메모리 요약 정보"""
        episodic_count = self.repository.get_user_memory_count(user_id, MemoryType.EPISODIC)
        semantic_count = self.repository.get_user_memory_count(user_id, MemoryType.SEMANTIC)
        
        total_memories = episodic_count + semantic_count
        
        return {
            "user_id": user_id,
            "total_memories": total_memories,
            "episodic_count": episodic_count,
            "semantic_count": semantic_count,
            "memory_distribution": {
                "episodic_ratio": episodic_count / max(total_memories, 1),
                "semantic_ratio": semantic_count / max(total_memories, 1)
            },
            "classification_service_threshold": self.classification_service.get_classification_confidence_threshold()
        }
    
    def delete_user_memories(
        self, 
        user_id: str, 
        memory_type: Optional[MemoryType] = None
    ) -> Dict[str, Any]:
        """사용자 메모리 삭제"""
        try:
            # 삭제 전 카운트 조회
            before_summary = self.get_user_memory_summary(user_id)
            
            # 삭제 실행
            self.repository.delete_user_memories(user_id, memory_type)
            
            # 삭제 후 카운트 조회
            after_summary = self.get_user_memory_summary(user_id)
            
            deleted_count = before_summary["total_memories"] - after_summary["total_memories"]
            
            return {
                "user_id": user_id,
                "deleted_memory_type": memory_type.value if memory_type else "all",
                "deleted_count": deleted_count,
                "remaining_count": after_summary["total_memories"],
                "success": True
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
    
    # === 분류 관련 메서드 ===
    
    def classify_memory(self, text: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """메모리 분류만 수행 (실제 삽입하지 않음)"""
        return self.classification_service.classify_memory(text, metadata or {})
    
    def batch_classify_memories(self, texts: List[str], metadata_list: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """배치 메모리 분류"""
        return self.classification_service.batch_classify(texts, metadata_list)
    
    def should_request_manual_classification(self, text: str, metadata: Dict[str, Any] = None) -> bool:
        """수동 분류 필요 여부 판단"""
        classification = self.classification_service.classify_memory(text, metadata or {})
        return self.classification_service.should_request_manual_classification(classification)
    
    # === Private Helper Methods ===
    
    def _build_memory_data(self, text: str, embedding: List[float], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """메모리 데이터 구성"""
        return {
            "text": text,
            "embedding": embedding,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "importance_score": metadata.get("importance_score", 0.5),
            "source": metadata.get("source", "facade_service"),
            **metadata  # 추가 메타데이터
        }
    
    def _calculate_search_weights(self, classification: Dict[str, Any]) -> Dict[MemoryType, float]:
        """검색 가중치 계산"""
        predicted_type = classification["predicted_type"]
        confidence = classification["confidence"]
        
        if predicted_type == MemoryType.EPISODIC:
            return {
                MemoryType.EPISODIC: 1.0 + confidence * 0.5,
                MemoryType.SEMANTIC: 1.0 - confidence * 0.3
            }
        else:
            return {
                MemoryType.EPISODIC: 1.0 - confidence * 0.3,
                MemoryType.SEMANTIC: 1.0 + confidence * 0.5
            }