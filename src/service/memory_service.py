from src.repository.base import VectorDBRepository
from src.models import InsertRequest, InsertResponse, SearchRequest, SearchResult
from src.models.memory_point import MemoryPoint
from datetime import datetime, timezone
from typing import List
from src.utils import VectorDBConnectionError, InvalidRequestError
from src.utils.time import parse_iso_time, calculate_time_weight
from src.service.embedding import EmbeddingService
from src.config.settings import db_config



class MemoryService:

    SEARCH_CANDIDATE_MULTIPLIER = 3
    MAX_SEARCH_CANDIDATES = 50

    """비즈니스 로직(삽입, 검색, 시간 가중치 등)을 담당하는 서비스 계층."""
    def __init__(self, embedding_service: EmbeddingService, repository: VectorDBRepository):
        """임베딩 서비스와 벡터DB 레포지토리 주입."""
        self.embedding_service = embedding_service
        self.repository = repository

    def _encode_text(self, text: str) -> list:
        """텍스트를 벡터로 변환 (임베딩)."""
        return self.embedding_service.encode(text)

    def _make_metadata(self, req: InsertRequest, timestamp: str) -> dict:
        """입력 요청과 timestamp로 메타데이터 딕셔너리 생성."""
        return {
            "text": req.text,
            "timestamp": timestamp,
            **req.metadata
        }

    def _make_point(self, vector: list, metadata: dict) -> MemoryPoint:
        """벡터와 메타데이터로 MemoryPoint 생성."""
        return MemoryPoint(vector=vector, metadata=metadata)

    def insert(self, req: InsertRequest, collection_name=None) -> InsertResponse:
        """텍스트 및 메타데이터를 벡터로 변환 후 DB에 삽입."""
        if not req.text:
            raise InvalidRequestError("text 필드는 필수입니다.")
        
        timestamp = req.timestamp if req.timestamp else datetime.now(timezone.utc).isoformat()
        req.timestamp = timestamp
        
        vector = self._encode_text(req.text)
        metadata = self._make_metadata(req, timestamp)
        point = self._make_point(vector, metadata)
        
        try:
            self.repository.upsert(point, collection_name=collection_name)
        except Exception as e:
            raise VectorDBConnectionError(f"DB upsert 실패: {e}")
        return InsertResponse(status="ok", timestamp=req.timestamp)

    def search(self, req: SearchRequest, collection_name=None) -> List[SearchResult]:
        """쿼리 벡터와 시간 가중치로 유사도 검색 결과 반환."""
        if not req.query:
            raise InvalidRequestError("query 필드는 필수입니다.")
        
        reference_time = parse_iso_time(req.reference_time) if req.reference_time else datetime.now(timezone.utc)
        query_vector = self._encode_text(req.query)
        search_limit = min(req.top_k * self.SEARCH_CANDIDATE_MULTIPLIER, self.MAX_SEARCH_CANDIDATES)
        
        try:
            results = self.repository.search(query_vector, search_limit, collection_name=collection_name)
        except Exception as e:
            raise VectorDBConnectionError(f"DB 검색 실패: {e}")
        
        weighted_results = [
            self._make_search_result(result, reference_time, req.time_weight)
            for result in results
        ]
        weighted_results.sort(key=lambda x: x.final_score, reverse=True)
        return weighted_results[:req.top_k]

    def _make_search_result(self, result: MemoryPoint, reference_time, time_weight) -> SearchResult:
        """MemoryPoint에서 시간 가중치와 최종 점수를 계산해 SearchResult로 변환."""
        payload = result.metadata
        similarity_score = payload.get('similarity_score', 1.0)
        if "timestamp" in payload:
            insert_time = parse_iso_time(payload["timestamp"])
            t_weight = calculate_time_weight(insert_time, reference_time, time_weight)
        else:
            t_weight = 0.5
        final_score = similarity_score * t_weight
        return SearchResult(
            text=payload.get("text"),
            similarity_score=similarity_score,
            time_weight=t_weight,
            final_score=final_score,
            timestamp=payload.get("timestamp"),
            metadata={k: v for k, v in payload.items() if k not in ["text", "timestamp", "similarity_score"]}
        ) 

    def get_collection_stats(self, collection_name=None):
        return self.repository.get_collection_stats(collection_name=collection_name)

    def reset_collection(self, collection_name=None, vector_dim=None):
        """Qdrant 컬렉션을 삭제 후 재생성합니다."""
        self.repository.reset_collection(collection_name=collection_name, vector_dim=vector_dim) 