"""
메모리 서비스 - 하위 호환성을 위한 래퍼
새로운 아키텍처(Facade 패턴)으로 위임하되 기존 API 유지
"""
from typing import List, Dict, Any, Optional
from src.service.memory_facade import MemoryFacadeService
from src.config.settings import MemoryType
from src.models.memory_point import MemoryPoint

class MemoryService:
    """다중 컬렉션 메모리 서비스 - 하위 호환성 래퍼"""
    
    def __init__(self):
        # 새로운 Facade 서비스로 위임
        self._facade = MemoryFacadeService()
    
    def insert_memory_with_auto_classification(
        self, 
        text: str, 
        user_id: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """자동 분류를 통한 메모리 삽입 - Facade로 위임"""
        return self._facade.insert_memory_with_auto_classification(text, user_id, metadata)
    
    def insert_memory_with_manual_type(
        self,
        text: str,
        user_id: str,
        memory_type: MemoryType,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """수동 지정된 타입으로 메모리 삽입 - Facade로 위임"""
        result = self._facade.insert_memory_with_manual_type(text, user_id, memory_type, metadata)
        return result["id"]  # 하위 호환성을 위해 ID만 반환
    
    def search_memory_single_collection(
        self,
        query: str,
        user_id: str,
        memory_type: MemoryType,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[MemoryPoint]:
        """단일 컬렉션에서 메모리 검색 - Facade로 위임"""
        return self._facade.search_memory_single_collection(query, user_id, memory_type, limit, filters)
    
    def search_memory_multi_collection(
        self,
        query: str,
        user_id: str,
        collections: List[MemoryType] = None,
        limit: int = 10,
        weights: Optional[Dict[MemoryType, float]] = None
    ) -> List[MemoryPoint]:
        """다중 컬렉션 통합 검색 - Facade로 위임"""
        return self._facade.search_memory_multi_collection(query, user_id, collections, limit, weights)
    
    def get_intelligent_search_weights(self, query: str) -> Dict[MemoryType, float]:
        """쿼리 분석을 통한 지능형 가중치 결정 - Facade로 위임"""
        classification = self._facade.classify_memory(query)
        return self._facade._calculate_search_weights(classification)
    
    def search_with_intelligent_weights(
        self,
        query: str,
        user_id: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """지능형 가중치를 사용한 검색 - Facade로 위임"""
        return self._facade.search_with_intelligent_weights(query, user_id, limit)
    
    def get_user_memory_summary(self, user_id: str) -> Dict[str, Any]:
        """사용자 메모리 요약 정보 - Facade로 위임"""
        return self._facade.get_user_memory_summary(user_id)
    
    def classify_existing_memory(self, memory_id: str, text: str) -> Dict[str, Any]:
        """기존 메모리의 분류 재검토 - Facade로 위임"""
        classification = self._facade.classify_memory(text, {})
        
        return {
            "memory_id": memory_id,
            "current_classification": classification,
            "explanation": classification["explanation"],
            "should_reclassify": classification["confidence"] > 0.7
        }
    
    def batch_reclassify_memories(
        self, 
        user_id: str, 
        memory_type: MemoryType,
        confidence_threshold: float = 0.8
    ) -> Dict[str, Any]:
        """배치 재분류 (마이그레이션용) - 임시 구현"""
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
        """사용자 메모리 삭제 - Facade로 위임"""
        return self._facade.delete_user_memories(user_id, memory_type)
    
    def reset_collection(self, memory_type: MemoryType) -> Dict[str, Any]:
        """컬렉션 초기화 - Facade로 위임"""
        return self._facade.reset_collection(memory_type)
    
    def get_collection_stats(self, memory_type: MemoryType) -> Dict[str, Any]:
        """컬렉션 통계 정보 - Facade로 위임"""
        return self._facade.get_collection_stats(memory_type)