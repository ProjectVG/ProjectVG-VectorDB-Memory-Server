from typing import List, Dict, Optional, Tuple
from datetime import datetime, timezone, timedelta
import numpy as np
from src.models import InsertRequest, SearchRequest, SearchResult, InsertResponse, AdvancedSearchRequest, MemoryMetadata
from src.models.memory_point import MemoryPoint
from src.service.advanced_memory_service import AdvancedMemoryService
from src.service.query_analyzer import QueryAnalyzer, QueryIntent
from src.utils import InvalidRequestError

class IntelligentMemoryService(AdvancedMemoryService):
    """지능형 메모리 서비스 - 2단계 검색 시스템"""
    
    def __init__(self, embedding_service, repository, query_analyzer: QueryAnalyzer):
        super().__init__(embedding_service, repository)
        self.query_analyzer = query_analyzer
    
    def intelligent_search(self, query: str, user_id: str = "anonymous") -> List[SearchResult]:
        """지능형 검색 - 2단계 프로세스"""
        
        # 1단계: 쿼리 분석
        query_intent = self.query_analyzer.analyze_query(query)
        print(f"쿼리 분석 결과: {query_intent}")
        
        # 2단계: 분석 결과를 바탕으로 검색 전략 결정
        search_strategy = self._determine_search_strategy(query_intent)
        
        # 3단계: 전략에 따른 검색 실행
        results = self._execute_search_strategy(query_intent, search_strategy, user_id)
        
        return results
    
    def _determine_search_strategy(self, query_intent: QueryIntent) -> str:
        """쿼리 의도에 따른 검색 전략 결정"""
        
        # 시간 참조가 있으면 시간 기반 검색
        if query_intent.time_references:
            return "temporal"
        
        # 개체명이 있으면 컨텍스트 기반 검색
        if query_intent.entities:
            return "contextual"
        
        # 액션 타입에 따른 검색
        if query_intent.action_type == "recall":
            return "semantic"
        elif query_intent.action_type == "compare":
            return "hybrid"
        elif query_intent.action_type == "summarize":
            return "semantic"
        
        # 기본값
        return "hybrid"
    
    def _execute_search_strategy(self, query_intent: QueryIntent, strategy: str, user_id: str) -> List[SearchResult]:
        """검색 전략 실행"""
        
        if strategy == "temporal":
            return self._temporal_search(query_intent, user_id)
        elif strategy == "contextual":
            return self._contextual_search(query_intent, user_id)
        elif strategy == "semantic":
            return self._semantic_search(query_intent, user_id)
        elif strategy == "hybrid":
            return self._hybrid_search(query_intent, user_id)
        else:
            return self._semantic_search(query_intent, user_id)
    
    def _temporal_search(self, query_intent: QueryIntent, user_id: str) -> List[SearchResult]:
        """시간 기반 검색"""
        results = []
        
        for time_ref in query_intent.time_references:
            start_date, end_date = time_ref["date_range"]
            
            # 시간 범위 내의 메모리 검색
            for memory_type in self.memory_types.keys():
                collection_name = f"user_{user_id}_{memory_type}_memories"
                
                try:
                    # 시간 필터링된 검색
                    time_filtered_results = self._search_with_time_filter(
                        query_intent.extracted_keywords,
                        collection_name,
                        start_date,
                        end_date
                    )
                    results.extend(time_filtered_results)
                except:
                    continue
        
        # 시간 가중치 적용
        for result in results:
            if result.timestamp:
                time_diff = (datetime.now(timezone.utc) - datetime.fromisoformat(result.timestamp)).days
                time_weight = np.exp(-0.1 * time_diff)
                result.final_score *= time_weight
        
        return sorted(results, key=lambda x: x.final_score, reverse=True)[:5]
    
    def _contextual_search(self, query_intent: QueryIntent, user_id: str) -> List[SearchResult]:
        """컨텍스트 기반 검색"""
        results = []
        
        # 개체명 기반 검색
        for entity in query_intent.entities:
            entity_keywords = [entity["value"]]
            
            for memory_type in self.memory_types.keys():
                collection_name = f"user_{user_id}_{memory_type}_memories"
                
                try:
                    # 개체명 관련 메모리 검색
                    entity_results = self._search_with_entity_filter(
                        entity_keywords,
                        collection_name,
                        entity
                    )
                    results.extend(entity_results)
                except:
                    continue
        
        return sorted(results, key=lambda x: x.final_score, reverse=True)[:5]
    
    def _semantic_search(self, query_intent: QueryIntent, user_id: str) -> List[SearchResult]:
        """의미적 검색"""
        results = []
        
        # 모든 메모리 타입에서 의미적 검색
        for memory_type in self.memory_types.keys():
            collection_name = f"user_{user_id}_{memory_type}_memories"
            
            try:
                # 벡터 기반 검색
                semantic_results = self._search_semantic(
                    query_intent.extracted_keywords,
                    collection_name
                )
                results.extend(semantic_results)
            except:
                continue
        
        return sorted(results, key=lambda x: x.final_score, reverse=True)[:5]
    
    def _hybrid_search(self, query_intent: QueryIntent, user_id: str) -> List[SearchResult]:
        """하이브리드 검색"""
        semantic_results = self._semantic_search(query_intent, user_id)
        keyword_results = self._keyword_search(query_intent.original_query, user_id)
        
        # 결과 결합
        combined_results = self._combine_search_results(
            semantic_results, keyword_results, 0.7
        )
        
        return combined_results[:5]
    
    def _search_with_time_filter(self, keywords: List[str], collection_name: str, 
                                start_date: datetime, end_date: datetime) -> List[SearchResult]:
        """시간 필터링된 검색"""
        # 실제 구현에서는 Qdrant의 필터링 기능 사용
        # 여기서는 간단한 구현
        all_memories = self._get_all_memories(collection_name)
        filtered_memories = []
        
        for memory in all_memories:
            memory_timestamp = memory.metadata.get("timestamp")
            if memory_timestamp:
                memory_date = datetime.fromisoformat(memory_timestamp)
                if start_date <= memory_date <= end_date:
                    # 키워드 매칭 확인
                    memory_text = memory.metadata.get("text", "")
                    if any(keyword in memory_text for keyword in keywords):
                        filtered_memories.append(memory)
        
        # SearchResult로 변환
        results = []
        for memory in filtered_memories:
            result = SearchResult(
                text=memory.metadata.get("text"),
                similarity_score=0.8,  # 기본값
                time_weight=1.0,
                final_score=0.8,
                timestamp=memory.metadata.get("timestamp"),
                metadata=memory.metadata
            )
            results.append(result)
        
        return results
    
    def _search_with_entity_filter(self, keywords: List[str], collection_name: str, 
                                  entity: Dict) -> List[SearchResult]:
        """개체명 필터링된 검색"""
        all_memories = self._get_all_memories(collection_name)
        filtered_memories = []
        
        for memory in all_memories:
            memory_text = memory.metadata.get("text", "")
            memory_entities = memory.metadata.get("entities", [])
            
            # 개체명 매칭 확인
            entity_matched = any(
                entity["value"] == mem_entity.get("value") 
                for mem_entity in memory_entities
            )
            
            # 키워드 매칭 확인
            keyword_matched = any(keyword in memory_text for keyword in keywords)
            
            if entity_matched or keyword_matched:
                filtered_memories.append(memory)
        
        # SearchResult로 변환
        results = []
        for memory in filtered_memories:
            result = SearchResult(
                text=memory.metadata.get("text"),
                similarity_score=0.9 if entity_matched else 0.7,
                time_weight=1.0,
                final_score=0.9 if entity_matched else 0.7,
                timestamp=memory.metadata.get("timestamp"),
                metadata=memory.metadata
            )
            results.append(result)
        
        return results
    
    def _search_semantic(self, keywords: List[str], collection_name: str) -> List[SearchResult]:
        """의미적 검색"""
        # 벡터 기반 검색 구현
        query_text = " ".join(keywords)
        query_vector = self._encode_text(query_text)
        
        try:
            results = self.repository.search(query_vector, 10, collection_name=collection_name)
            
            # SearchResult로 변환
            search_results = []
            for result in results:
                search_result = SearchResult(
                    text=result.metadata.get("text"),
                    similarity_score=0.8,  # 실제로는 벡터 유사도 계산
                    time_weight=1.0,
                    final_score=0.8,
                    timestamp=result.metadata.get("timestamp"),
                    metadata=result.metadata
                )
                search_results.append(search_result)
            
            return search_results
        except:
            return []
    
    def _keyword_search(self, query: str, user_id: str) -> List[SearchResult]:
        """키워드 검색"""
        keywords = self._extract_keywords(query)
        results = []
        
        for memory_type in self.memory_types.keys():
            collection_name = f"user_{user_id}_{memory_type}_memories"
            
            try:
                keyword_results = self._keyword_search_in_collection(keywords, collection_name)
                results.extend(keyword_results)
            except:
                continue
        
        return results
    
    def _keyword_search_in_collection(self, keywords: List[str], collection_name: str) -> List[SearchResult]:
        """컬렉션 내 키워드 검색"""
        all_memories = self._get_all_memories(collection_name)
        results = []
        
        for memory in all_memories:
            memory_text = memory.metadata.get("text", "")
            keyword_score = self._calculate_keyword_score(memory_text, keywords)
            
            if keyword_score > 0:
                result = SearchResult(
                    text=memory_text,
                    similarity_score=keyword_score,
                    time_weight=1.0,
                    final_score=keyword_score,
                    timestamp=memory.metadata.get("timestamp"),
                    metadata=memory.metadata
                )
                results.append(result)
        
        return results
    
    def insert_with_intelligent_analysis(self, text: str, user_id: str = "anonymous") -> InsertResponse:
        """지능형 분석을 통한 메모리 삽입"""
        
        # 1. 텍스트 분석
        query_intent = self.query_analyzer.analyze_query(text)
        
        # 2. 메모리 타입 자동 결정
        memory_type = self._determine_memory_type(query_intent)
        
        # 3. 메타데이터 생성
        metadata = self._create_intelligent_metadata(query_intent, user_id)
        
        # 4. 메모리 삽입
        req = InsertRequest(
            text=text,
            user_id=user_id,
            metadata=metadata
        )
        
        return self.insert_with_type_and_user(req, memory_type)
    
    def _determine_memory_type(self, query_intent: QueryIntent) -> str:
        """쿼리 의도에 따른 메모리 타입 결정"""
        
        # 감정적 컨텍스트가 있으면 감정적 메모리
        if query_intent.context.get("emotional_context"):
            return "emotional"
        
        # 시간 참조가 있으면 개인 경험 메모리
        if query_intent.time_references:
            return "episodic"
        
        # 개체명이 있으면 상황별 메모리
        if query_intent.entities:
            return "contextual"
        
        # 절차적 키워드가 있으면 절차적 메모리
        procedural_keywords = ["방법", "순서", "단계", "과정", "절차"]
        if any(keyword in query_intent.original_query for keyword in procedural_keywords):
            return "procedural"
        
        # 기본값
        return "semantic"
    
    def _create_intelligent_metadata(self, query_intent: QueryIntent, user_id: str) -> Dict:
        """지능형 메타데이터 생성"""
        metadata = {
            "user_id": user_id,
            "entities": query_intent.entities,
            "context": query_intent.context,
            "importance": self._calculate_importance(query_intent.original_query),
            "intent_type": query_intent.intent_type,
            "action_type": query_intent.action_type,
            "time_references": query_intent.time_references,
            "extracted_keywords": query_intent.extracted_keywords,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        return metadata 