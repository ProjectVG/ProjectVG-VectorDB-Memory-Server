from src.repository import VectorDBRepository
from src.models import InsertRequest, InsertResponse, SearchRequest, SearchResult
from sentence_transformers import SentenceTransformer
from qdrant_client.models import PointStruct
import uuid
from datetime import datetime, timezone
from typing import List
from src.utils import ModelEncodeError, VectorDBConnectionError, InvalidRequestError
from src.utils.time import parse_iso_time, calculate_time_weight

class MemoryService:
    """비즈니스 로직(삽입, 검색, 시간 가중치 등)을 담당하는 서비스 계층."""
    def __init__(self, model: SentenceTransformer, repository: VectorDBRepository):
        self.model = model
        self.repository = repository

    def _encode_text(self, text: str) -> list:
        try:
            return self.model.encode(text).tolist()
        except Exception as e:
            raise ModelEncodeError(f"임베딩 모델 인코딩 실패: {e}")

    def _make_metadata(self, req: InsertRequest, insert_time: datetime) -> dict:
        return {
            "text": req.text,
            "timestamp": req.timestamp,
            "insert_time": insert_time.isoformat(),
            **req.metadata
        }

    def _make_point(self, vector: list, metadata: dict) -> PointStruct:
        return PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload=metadata
        )

    def insert(self, req: InsertRequest) -> InsertResponse:
        if not req.text:
            raise InvalidRequestError("text 필드는 필수입니다.")
        insert_time = parse_iso_time(req.timestamp) if req.timestamp else datetime.now(timezone.utc)
        req.timestamp = insert_time.isoformat()
        vector = self._encode_text(req.text)
        metadata = self._make_metadata(req, insert_time)
        point = self._make_point(vector, metadata)
        try:
            self.repository.upsert(point)
        except Exception as e:
            raise VectorDBConnectionError(f"Qdrant upsert 실패: {e}")
        return InsertResponse(status="ok", timestamp=req.timestamp)

    def search(self, req: SearchRequest) -> List[SearchResult]:
        if not req.query:
            raise InvalidRequestError("query 필드는 필수입니다.")
        reference_time = parse_iso_time(req.reference_time) if req.reference_time else datetime.now(timezone.utc)
        query_vector = self._encode_text(req.query)
        search_limit = min(req.top_k * 3, 50)
        try:
            results = self.repository.search(query_vector, search_limit)
        except Exception as e:
            raise VectorDBConnectionError(f"Qdrant 검색 실패: {e}")
        weighted_results = [
            self._make_search_result(result, reference_time, req.time_weight)
            for result in results
        ]
        weighted_results.sort(key=lambda x: x.final_score, reverse=True)
        return weighted_results[:req.top_k]

    def _make_search_result(self, result, reference_time, time_weight) -> SearchResult:
        similarity_score = result.score
        payload = result.payload
        if "insert_time" in payload:
            insert_time = parse_iso_time(payload["insert_time"])
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
            metadata={k: v for k, v in payload.items() if k not in ["text", "timestamp", "insert_time"]}
        ) 