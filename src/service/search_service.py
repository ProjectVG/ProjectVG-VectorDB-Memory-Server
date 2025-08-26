"""
검색 서비스
- 단일 책임: 메모리 검색만 담당
- 다양한 검색 전략을 제공
"""
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import numpy as np
from src.models.memory_point import MemoryPoint
from src.config.settings import MemoryType
from src.repository.memory_repository import MemoryQdrantRepository
from src.infra.embedding import OpenAIEmbeddingService


class MemorySearchService:
    """메모리 검색 전문 서비스"""
    
    def __init__(self):
        self.repository = MemoryQdrantRepository()
        self.embedding_service = OpenAIEmbeddingService()
    
    def search_single_collection(
        self,
        query: str,
        user_id: str,
        memory_type: MemoryType,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[MemoryPoint]:
        """단일 컬렉션 검색"""
        query_vector = self.embedding_service.get_embedding(query)
        return self.repository.search_memory(
            query_vector, user_id, memory_type, limit, filters
        )
    
    def search_multi_collection(
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
        
        query_vector = self.embedding_service.get_embedding(query)
        return self.repository.multi_collection_search(
            query_vector, user_id, collections, limit, weights
        )
    
    def time_weighted_search(
        self,
        query: str,
        user_id: str,
        memory_type: MemoryType,
        limit: int = 10,
        decay_factor: float = 0.1,
        time_weight_ratio: float = 0.3
    ) -> List[MemoryPoint]:
        """시간 가중치 검색"""
        # 기본 검색 실행
        results = self.search_single_collection(query, user_id, memory_type, limit * 2)
        
        # 시간 가중치 적용
        reference_time = datetime.now(timezone.utc)
        
        for result in results:
            if hasattr(result, 'timestamp') and result.timestamp:
                try:
                    memory_time = datetime.fromisoformat(result.timestamp.replace('Z', '+00:00'))
                    time_diff_days = (reference_time - memory_time).days
                    time_weight = np.exp(-decay_factor * time_diff_days)
                    
                    # 기존 점수와 시간 가중치 결합
                    original_score = result.score if hasattr(result, 'score') else 1.0
                    result.score = (1 - time_weight_ratio) * original_score + time_weight_ratio * time_weight
                except:
                    # 시간 파싱 실패 시 기본 점수 유지
                    pass
        
        # 점수 기준으로 정렬하고 limit 적용
        sorted_results = sorted(results, key=lambda x: getattr(x, 'score', 0), reverse=True)
        return sorted_results[:limit]
    
    def similarity_search_with_threshold(
        self,
        query: str,
        user_id: str,
        memory_type: MemoryType,
        similarity_threshold: float = 0.7,
        limit: int = 10
    ) -> List[MemoryPoint]:
        """유사도 임계값 기반 검색"""
        results = self.search_single_collection(query, user_id, memory_type, limit * 2)
        
        # 임계값 이상의 결과만 필터링
        filtered_results = [
            result for result in results 
            if getattr(result, 'score', 0) >= similarity_threshold
        ]
        
        return filtered_results[:limit]
    
    def contextual_search(
        self,
        query: str,
        user_id: str,
        context: Dict[str, Any],
        limit: int = 10
    ) -> List[MemoryPoint]:
        """컨텍스트 기반 검색"""
        # 컨텍스트에 따라 검색 전략 결정
        if context.get("time_sensitive", False):
            return self.time_weighted_search(
                query, user_id, MemoryType.EPISODIC, limit, 
                decay_factor=context.get("decay_factor", 0.1)
            )
        
        if context.get("memory_type"):
            return self.search_single_collection(
                query, user_id, context["memory_type"], limit
            )
        
        # 기본적으로 다중 컬렉션 검색
        return self.search_multi_collection(query, user_id, limit=limit)
    
    def semantic_similarity_search(
        self,
        reference_memory_id: str,
        user_id: str,
        memory_type: MemoryType,
        limit: int = 10
    ) -> List[MemoryPoint]:
        """특정 메모리와 유사한 메모리 검색"""
        # 참조 메모리 가져오기
        reference_memory = self.repository.get_memory_by_id(reference_memory_id, memory_type)
        if not reference_memory:
            return []
        
        # 참조 메모리의 벡터로 검색
        return self.repository.search_memory(
            reference_memory.vector, user_id, memory_type, limit
        )


class IntelligentSearchService:
    """지능형 검색 서비스 - 쿼리 분석 기반 최적 검색"""
    
    def __init__(self):
        self.search_service = MemorySearchService()
        self.embedding_service = OpenAIEmbeddingService()
    
    def intelligent_search(
        self,
        query: str,
        user_id: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """쿼리 분석 기반 지능형 검색"""
        # 쿼리 분석
        query_analysis = self._analyze_query(query)
        
        # 분석 결과에 따른 검색 전략 결정
        search_strategy = self._determine_search_strategy(query_analysis)
        
        # 검색 실행
        results = self._execute_search_strategy(query, user_id, search_strategy, limit)
        
        return {
            "results": results,
            "query_analysis": query_analysis,
            "search_strategy": search_strategy,
            "explanation": self._generate_search_explanation(query_analysis, search_strategy)
        }
    
    def _analyze_query(self, query: str) -> Dict[str, Any]:
        """쿼리 특성 분석"""
        analysis = {
            "has_time_reference": bool(re.search(r'\b(오늘|어제|내일|최근|이전|언제)\b', query)),
            "has_emotion_words": bool(re.search(r'\b(기쁘|슬프|화나|좋|싫)\w*\b', query)),
            "is_question": query.strip().endswith('?') or any(q in query for q in ['뭐', '어떻', '언제', '어디']),
            "is_factual_query": bool(re.search(r'\b(정의|개념|사실|정보)\b', query)),
            "query_length": len(query.split()),
            "complexity": self._assess_query_complexity(query)
        }
        return analysis
    
    def _assess_query_complexity(self, query: str) -> str:
        """쿼리 복잡도 평가"""
        word_count = len(query.split())
        if word_count <= 2:
            return "simple"
        elif word_count <= 5:
            return "medium"
        else:
            return "complex"
    
    def _determine_search_strategy(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """검색 전략 결정"""
        strategy = {
            "type": "multi_collection",  # 기본값
            "weights": {MemoryType.EPISODIC: 1.0, MemoryType.SEMANTIC: 1.0},
            "use_time_weighting": False,
            "similarity_threshold": 0.6
        }
        
        # 시간 참조가 있으면 Episodic 가중치 증가 + 시간 가중치 사용
        if analysis["has_time_reference"]:
            strategy["weights"][MemoryType.EPISODIC] = 1.5
            strategy["use_time_weighting"] = True
        
        # 감정 표현이 있으면 Episodic 가중치 증가
        if analysis["has_emotion_words"]:
            strategy["weights"][MemoryType.EPISODIC] = 1.3
        
        # 사실적 쿼리면 Semantic 가중치 증가
        if analysis["is_factual_query"]:
            strategy["weights"][MemoryType.SEMANTIC] = 1.5
            strategy["similarity_threshold"] = 0.7  # 더 높은 정확도 요구
        
        # 질문 형태면 Episodic 선호
        if analysis["is_question"]:
            strategy["weights"][MemoryType.EPISODIC] = 1.2
        
        return strategy
    
    def _execute_search_strategy(
        self,
        query: str,
        user_id: str,
        strategy: Dict[str, Any],
        limit: int
    ) -> List[MemoryPoint]:
        """검색 전략 실행"""
        if strategy["use_time_weighting"]:
            # 시간 가중치 검색 (주로 Episodic)
            return self.search_service.time_weighted_search(
                query, user_id, MemoryType.EPISODIC, limit
            )
        else:
            # 다중 컬렉션 가중치 검색
            return self.search_service.search_multi_collection(
                query, user_id, 
                collections=[MemoryType.EPISODIC, MemoryType.SEMANTIC],
                limit=limit,
                weights=strategy["weights"]
            )
    
    def _generate_search_explanation(self, analysis: Dict[str, Any], strategy: Dict[str, Any]) -> str:
        """검색 전략 설명 생성"""
        explanations = []
        
        if analysis["has_time_reference"]:
            explanations.append("시간 참조로 인한 Episodic 메모리 가중치 증가")
        
        if analysis["has_emotion_words"]:
            explanations.append("감정 표현 감지로 인한 Episodic 메모리 선호")
        
        if analysis["is_factual_query"]:
            explanations.append("사실적 쿼리로 인한 Semantic 메모리 가중치 증가")
        
        if strategy["use_time_weighting"]:
            explanations.append("시간 가중치 적용으로 최근 메모리 우선")
        
        return "; ".join(explanations) if explanations else "기본 다중 컬렉션 검색 적용"