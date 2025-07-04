from fastapi import APIRouter, Depends
from src.models import InsertRequest, SearchRequest, InsertResponse, SearchResult
from src.config import settings
from src.repository.vector_db_repository import VectorDBRepository
from src.service.memory_service import MemoryService
from sentence_transformers import SentenceTransformer
from typing import List
from datetime import datetime, timezone

router = APIRouter()

def get_memory_service():
    vector_db = VectorDBRepository()
    model = SentenceTransformer(settings.model_name)
    return MemoryService(model, vector_db)

@router.post("/insert", response_model=InsertResponse)
def insert(req: InsertRequest, service: MemoryService = Depends(get_memory_service)):
    """텍스트 및 메타데이터를 벡터로 변환 후 DB에 삽입"""
    return service.insert(req)

@router.post("/search", response_model=List[SearchResult])
def search(req: SearchRequest, service: MemoryService = Depends(get_memory_service)):
    """검색 요청 처리"""
    return service.search(req)

@router.get("/time")
def get_current_time():
    """현재 서버 시간을 ISO 형식으로 반환"""
    return {"current_time": datetime.now(timezone.utc).isoformat()}

@router.get("/stats")
def get_collection_stats(service: MemoryService = Depends(get_memory_service)):
    """컬렉션의 통계 정보를 반환"""
    try:
        collection_info = service.repository.get_collection_stats()
        return {
            "collection_name": settings.collection_name,
            "vector_count": collection_info.points_count,
            "vector_size": collection_info.config.params.vectors.size,
            "distance": collection_info.config.params.vectors.distance.value
        }
    except Exception as e:
        return {"error": str(e)} 