from typing import List, Dict, Optional
from datetime import datetime, timezone
import numpy as np
from src.models import InsertRequest, SearchRequest, SearchResult, InsertResponse
from src.models.memory_point import MemoryPoint
from src.service.memory_service import MemoryService
from src.utils import InvalidRequestError

class AdvancedMemoryService(MemoryService):
    """고급 메모리 서비스 - 다양한 메모리 패턴 지원"""
    
    def __init__(self, embedding_service, repository):
        super().__init__(embedding_service, repository)
        self.memory_types = {
            "episodic": "개인 경험 기억",
            "semantic": "사실과 지식", 
            "procedural": "절차적 지식",
            "emotional": "감정적 기억",
            "contextual": "상황별 기억"
        }
    
    def insert_with_type_and_user(self, req: InsertRequest, memory_type: str = "semantic") -> InsertResponse:
        """메모리 타입과 사용자 ID를 지정하여 삽입"""
        if memory_type not in self.memory_types:
            raise InvalidRequestError(f"지원하지 않는 메모리 타입: {memory_type}")
        
        # 메타데이터에 메모리 타입과 사용자 ID 추가
        req.metadata["memory_type"] = memory_type
        req.metadata["user_id"] = req.user_id
        req.metadata["importance"] = self._calculate_importance(req.text)
        
        # 사용자별 컬렉션 생성
        collection_name = f"user_{req.user_id}_{memory_type}_memories"
        
        return self.insert(req, collection_name=collection_name)
    
    def search_by_user(self, req: SearchRequest, memory_type: str = None) -> List[SearchResult]:
        """사용자별 메모리 검색"""
        if memory_type:
            collection_name = f"user_{req.user_id}_{memory_type}_memories"
        else:
            # 모든 메모리 타입에서 검색
            all_results = []
            for mem_type in self.memory_types.keys():
                collection_name = f"user_{req.user_id}_{mem_type}_memories"
                try:
                    results = self.search(req, collection_name=collection_name)
                    all_results.extend(results)
                except:
                    continue
            
            # 점수순으로 정렬
            all_results.sort(key=lambda x: x.final_score, reverse=True)
            return all_results[:req.top_k]
        
        return self.search(req, collection_name=collection_name)
    
    def get_user_memory_stats(self, user_id: str) -> Dict[str, int]:
        """사용자별 메모리 통계"""
        stats = {}
        for mem_type in self.memory_types.keys():
            collection_name = f"user_{user_id}_{mem_type}_memories"
            try:
                collection_info = self.get_collection_stats(collection_name=collection_name)
                stats[mem_type] = collection_info.points_count
            except:
                stats[mem_type] = 0
        return stats
    
    def insert_with_type(self, req: InsertRequest, memory_type: str = "semantic") -> InsertResponse:
        """메모리 타입을 지정하여 삽입"""
        if memory_type not in self.memory_types:
            raise InvalidRequestError(f"지원하지 않는 메모리 타입: {memory_type}")
        
        # 메타데이터에 메모리 타입 추가
        req.metadata["memory_type"] = memory_type
        req.metadata["importance"] = self._calculate_importance(req.text)
        
        return self.insert(req, collection_name=f"{memory_type}_memories")
    
    def hybrid_search(self, req: SearchRequest, semantic_weight: float = 0.7) -> List[SearchResult]:
        """하이브리드 검색 (벡터 + 키워드)"""
        # 벡터 검색
        vector_results = self.search(req, collection_name=req.collection)
        
        # 키워드 검색 (간단한 구현)
        keyword_results = self._keyword_search(req.query, req.collection)
        
        # 결과 결합
        combined_results = self._combine_search_results(
            vector_results, keyword_results, semantic_weight
        )
        
        return combined_results[:req.top_k]
    
    def time_weighted_search(self, req: SearchRequest, decay_factor: float = 0.1) -> List[SearchResult]:
        """시간 가중치 검색"""
        results = self.search(req, collection_name=req.collection)
        
        reference_time = datetime.now(timezone.utc)
        
        for result in results:
            if result.timestamp:
                time_diff = (reference_time - datetime.fromisoformat(result.timestamp)).days
                time_weight = np.exp(-decay_factor * time_diff)
                result.final_score *= time_weight
        
        return sorted(results, key=lambda x: x.final_score, reverse=True)[:req.top_k]
    
    def memory_consolidation(self, collection_name: str, similarity_threshold: float = 0.8):
        """메모리 압축 및 통합"""
        # 모든 메모리 가져오기
        all_memories = self._get_all_memories(collection_name)
        
        # 유사한 메모리 그룹화
        memory_groups = self._group_similar_memories(all_memories, similarity_threshold)
        
        # 각 그룹에서 대표 메모리 선택
        consolidated_memories = []
        for group in memory_groups:
            representative = self._select_representative_memory(group)
            consolidated_memories.append(representative)
        
        return consolidated_memories
    
    def _calculate_importance(self, text: str) -> float:
        """텍스트 중요도 계산 (고급 구현)"""
        importance_score = 0.5  # 기본값
        
        # 1. 키워드 기반 중요도
        important_keywords = ["중요", "필수", "주의", "경고", "핵심", "긴급", "필수적"]
        urgent_keywords = ["즉시", "당장", "지금", "바로"]
        
        for keyword in important_keywords:
            if keyword in text:
                importance_score += 0.1
        
        for keyword in urgent_keywords:
            if keyword in text:
                importance_score += 0.2
        
        # 2. 텍스트 길이 기반 중요도
        if len(text) > 100:
            importance_score += 0.1  # 긴 텍스트는 더 중요할 수 있음
        
        # 3. 특수문자 기반 중요도 (강조 표시)
        emphasis_chars = ["!", "?", "*", "**", "___"]
        for char in emphasis_chars:
            if char in text:
                importance_score += 0.05
        
        # 4. 감정 기반 중요도
        emotional_words = ["사랑", "미워", "기쁘", "슬프", "화나", "무서워"]
        for word in emotional_words:
            if word in text:
                importance_score += 0.15  # 감정적 내용은 더 중요
        
        return min(importance_score, 1.0)
    
    def _keyword_search(self, query: str, collection_name: str) -> List[SearchResult]:
        """키워드 기반 검색 (고급 구현)"""
        # 실제 구현에서는 Elasticsearch나 다른 검색 엔진 사용
        # 여기서는 간단한 키워드 매칭 구현
        
        # 1. 쿼리에서 키워드 추출
        keywords = self._extract_keywords(query)
        
        # 2. 모든 메모리에서 키워드 검색
        all_memories = self._get_all_memories(collection_name)
        keyword_results = []
        
        for memory in all_memories:
            memory_text = memory.metadata.get("text", "")
            keyword_score = self._calculate_keyword_score(memory_text, keywords)
            
            if keyword_score > 0:
                # SearchResult 객체 생성
                result = SearchResult(
                    text=memory_text,
                    similarity_score=keyword_score,
                    time_weight=1.0,
                    final_score=keyword_score,
                    timestamp=memory.metadata.get("timestamp"),
                    metadata=memory.metadata
                )
                keyword_results.append(result)
        
        return keyword_results
    
    def _extract_keywords(self, query: str) -> List[str]:
        """쿼리에서 키워드 추출"""
        # 간단한 키워드 추출 (실제로는 NLP 라이브러리 사용)
        stop_words = ["이", "가", "을", "를", "의", "에", "로", "와", "과", "도", "는", "을", "를"]
        words = query.split()
        keywords = [word for word in words if word not in stop_words and len(word) > 1]
        return keywords
    
    def _calculate_keyword_score(self, text: str, keywords: List[str]) -> float:
        """키워드 매칭 점수 계산"""
        score = 0.0
        text_lower = text.lower()
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in text_lower:
                # 키워드 길이에 따른 가중치
                weight = len(keyword) / 10.0
                score += weight
        
        return min(score, 1.0)
    
    def _combine_search_results(self, vector_results: List[SearchResult], 
                              keyword_results: List[SearchResult], 
                              semantic_weight: float) -> List[SearchResult]:
        """검색 결과 결합"""
        combined = []
        
        # 벡터 검색 결과에 가중치 적용
        for result in vector_results:
            result.final_score *= semantic_weight
            combined.append(result)
        
        # 키워드 검색 결과에 가중치 적용
        keyword_weight = 1.0 - semantic_weight
        for result in keyword_results:
            result.final_score *= keyword_weight
            combined.append(result)
        
        return sorted(combined, key=lambda x: x.final_score, reverse=True)
    
    def _get_all_memories(self, collection_name: str) -> List[MemoryPoint]:
        """컬렉션의 모든 메모리 가져오기"""
        # 실제 구현에서는 페이지네이션 필요
        return []
    
    def _group_similar_memories(self, memories: List[MemoryPoint], 
                               threshold: float) -> List[List[MemoryPoint]]:
        """유사한 메모리 그룹화"""
        groups = []
        used = set()
        
        for i, memory in enumerate(memories):
            if i in used:
                continue
            
            group = [memory]
            used.add(i)
            
            for j, other_memory in enumerate(memories[i+1:], i+1):
                if j in used:
                    continue
                
                similarity = self._calculate_similarity(memory, other_memory)
                if similarity >= threshold:
                    group.append(other_memory)
                    used.add(j)
            
            groups.append(group)
        
        return groups
    
    def _calculate_similarity(self, memory1: MemoryPoint, memory2: MemoryPoint) -> float:
        """두 메모리 간 유사도 계산"""
        # 코사인 유사도 계산
        vec1 = np.array(memory1.vector)
        vec2 = np.array(memory2.vector)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        return dot_product / (norm1 * norm2)
    
    def _select_representative_memory(self, memory_group: List[MemoryPoint]) -> MemoryPoint:
        """그룹에서 대표 메모리 선택"""
        # 가장 높은 중요도를 가진 메모리 선택
        return max(memory_group, key=lambda m: m.metadata.get("importance", 0.5)) 