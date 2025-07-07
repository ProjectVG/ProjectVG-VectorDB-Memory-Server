from src.repository import VectorDBRepository
from src.models import InsertRequest, InsertResponse, SearchRequest, SearchResult
from qdrant_client.models import PointStruct
import uuid
from datetime import datetime, timezone
from typing import List
from src.utils import VectorDBConnectionError, InvalidRequestError
from src.utils.time import parse_iso_time, calculate_time_weight
from src.service.embedding import EmbeddingService

class MemoryService:
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

    def _make_point(self, vector: list, metadata: dict) -> PointStruct:
        """벡터와 메타데이터로 Qdrant PointStruct 생성."""
        return PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload=metadata
        )

    def insert(self, req: InsertRequest) -> InsertResponse:
        """텍스트 및 메타데이터를 벡터로 변환 후 DB에 삽입."""
        if not req.text:
            raise InvalidRequestError("text 필드는 필수입니다.")
        
        timestamp = req.timestamp if req.timestamp else datetime.now(timezone.utc).isoformat() # timestamp: 클라이언트 값이 있으면 사용, 없으면 서버 시간
        req.timestamp = timestamp
        
        vector = self._encode_text(req.text) # 텍스트 임베딩
        metadata = self._make_metadata(req, timestamp) # 메타데이터 생성
        point = self._make_point(vector, metadata) # Qdrant 포인트 생성
        
        try:
            self.repository.upsert(point)
        except Exception as e:
            raise VectorDBConnectionError(f"Qdrant upsert 실패: {e}")
        return InsertResponse(status="ok", timestamp=req.timestamp)

    def search(self, req: SearchRequest) -> List[SearchResult]:
        """쿼리 벡터와 시간 가중치로 유사도 검색 결과 반환."""
        if not req.query:
            raise InvalidRequestError("query 필드는 필수입니다.")
        
        reference_time = parse_iso_time(req.reference_time) if req.reference_time else datetime.now(timezone.utc) # 기준 시간: 클라이언트가 주면 사용, 없으면 현재 시간
        query_vector = self._encode_text(req.query) # 쿼리 임베딩
        search_limit = min(req.top_k * 3, 50) # 검색 제한 개수 설정

        try:
            results = self.repository.search(query_vector, search_limit)
        except Exception as e:
            raise VectorDBConnectionError(f"Qdrant 검색 실패: {e}")
        # 검색 결과별로 시간 가중치 적용 및 정렬
        weighted_results = [
            self._make_search_result(result, reference_time, req.time_weight)
            for result in results
        ]
        weighted_results.sort(key=lambda x: x.final_score, reverse=True)
        return weighted_results[:req.top_k]

    def _make_search_result(self, result, reference_time, time_weight) -> SearchResult:
        """Qdrant 검색 결과에서 시간 가중치와 최종 점수를 계산해 SearchResult로 변환."""
        similarity_score = result.score
        payload = result.payload
        # 검색 결과의 payload에서 timestamp를 추출하여 시간 가중치 계산에 사용
        if "timestamp" in payload:
            # timestamp가 있으면 이를 기준으로 시간 가중치 계산
            insert_time = parse_iso_time(payload["timestamp"])
            t_weight = calculate_time_weight(insert_time, reference_time, time_weight)
        else:
            # timestamp가 없으면 기본 가중치(0.5) 적용
            t_weight = 0.5
        # 최종 점수는 유사도 점수와 시간 가중치의 곱
        final_score = similarity_score * t_weight
        return SearchResult(
            text=payload.get("text"),
            similarity_score=similarity_score,
            time_weight=t_weight,
            final_score=final_score,
            timestamp=payload.get("timestamp"),
            metadata={k: v for k, v in payload.items() if k not in ["text", "timestamp"]}
        ) 