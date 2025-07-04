from src.repository.vector_db_repository import VectorDBRepository
from src.models import InsertRequest, InsertResponse, SearchRequest, SearchResult
from sentence_transformers import SentenceTransformer
from qdrant_client.models import PointStruct
import uuid
from datetime import datetime, timezone
import math
from typing import List

class MemoryService:
    """비즈니스 로직(삽입, 검색, 시간 가중치 등)을 담당하는 서비스 계층."""
    def __init__(self, model: SentenceTransformer, repository: VectorDBRepository):
        self.model = model
        self.repository = repository

    def calculate_time_weight(self, insert_time: datetime, reference_time: datetime, time_weight: float) -> float:
        """시간 가중치 계산."""
        if time_weight == 0.0:
            return 1.0
        time_diff = abs((reference_time - insert_time).total_seconds() / 86400)
        decay_factor = math.exp(-time_diff * time_weight)
        return decay_factor

    def parse_iso_time(self, time_str: str) -> datetime:
        """ISO 형식의 시간 문자열을 datetime 객체로 변환."""
        if time_str.endswith('Z'):
            time_str = time_str[:-1] + '+00:00'
        return datetime.fromisoformat(time_str)

    def insert(self, req: InsertRequest) -> InsertResponse:
        """텍스트 및 메타데이터를 벡터로 변환 후 DB에 삽입."""
        if req.timestamp:
            insert_time = self.parse_iso_time(req.timestamp)
        else:
            insert_time = datetime.now(timezone.utc)
            req.timestamp = insert_time.isoformat()
        vector = self.model.encode(req.text).tolist()
        metadata = {
            "text": req.text,
            "timestamp": req.timestamp,
            "insert_time": insert_time.isoformat(),
            **req.metadata
        }
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload=metadata
        )
        self.repository.upsert(point)
        return InsertResponse(status="ok", timestamp=req.timestamp)

    def search(self, req: SearchRequest) -> List[SearchResult]:
        """쿼리와 시간 가중치로 벡터 검색 및 결과 가공."""
        if req.reference_time:
            reference_time = self.parse_iso_time(req.reference_time)
        else:
            reference_time = datetime.now(timezone.utc)
        query_vector = self.model.encode(req.query).tolist()
        search_limit = min(req.top_k * 3, 50)
        results = self.repository.search(query_vector, search_limit)
        weighted_results = []
        for result in results:
            similarity_score = result.score
            payload = result.payload
            if "insert_time" in payload:
                insert_time = self.parse_iso_time(payload["insert_time"])
                time_weight = self.calculate_time_weight(insert_time, reference_time, req.time_weight)
            else:
                time_weight = 0.5
            final_score = similarity_score * time_weight
            weighted_results.append(SearchResult(
                text=payload.get("text"),
                similarity_score=similarity_score,
                time_weight=time_weight,
                final_score=final_score,
                timestamp=payload.get("timestamp"),
                metadata={k: v for k, v in payload.items() if k not in ["text", "timestamp", "insert_time"]}
            ))
        weighted_results.sort(key=lambda x: x.final_score, reverse=True)
        return weighted_results[:req.top_k] 