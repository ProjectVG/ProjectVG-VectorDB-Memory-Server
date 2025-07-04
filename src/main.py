from fastapi import FastAPI
from src.models import InsertRequest, SearchRequest, InsertResponse, SearchResult
from src.config import settings
from src.repository.vector_db_repository import VectorDBRepository
from src.service.memory_service import MemoryService
from sentence_transformers import SentenceTransformer
from datetime import datetime, timezone
from typing import List

vector_db = VectorDBRepository()
model = SentenceTransformer(settings.model_name)
memory_service = MemoryService(model, vector_db)

app = FastAPI()

COLLECTION_NAME = settings.collection_name

@app.post("/insert", response_model=InsertResponse)
def insert(req: InsertRequest):
    """텍스트 및 메타데이터를 벡터로 변환 후 DB에 삽입"""
    return memory_service.insert(req)

@app.post("/search", response_model=List[SearchResult])
def search(req: SearchRequest):
    """검색 요청 처리"""
    return memory_service.search(req)

@app.get("/time")
def get_current_time():
    """현재 서버 시간을 ISO 형식으로 반환"""
    return {"current_time": datetime.now(timezone.utc).isoformat()}

@app.get("/stats")
def get_collection_stats():
    """컬렉션의 통계 정보를 반환"""
    try:
        collection_info = vector_db.get_collection_stats()
        return {
            "collection_name": COLLECTION_NAME,
            "vector_count": collection_info.points_count,
            "vector_size": collection_info.config.params.vectors.size,
            "distance": collection_info.config.params.vectors.distance.value
        }
    except Exception as e:
        return {"error": str(e)} 