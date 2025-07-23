from fastapi import APIRouter, Depends
from src.models import InsertRequest, SearchRequest, InsertResponse, SearchResult
from src.config.settings import db_config
from src.service.factory import get_memory_service
from src.service.memory_service import MemoryService
from typing import List
from datetime import datetime, timezone

router = APIRouter()

def get_user_collection(user_id: str = None):
    if user_id:
        return f"user_{user_id}_vectors"
    return db_config.collection_name

@router.post("/insert", response_model=InsertResponse)
def insert(req: InsertRequest, service: MemoryService = Depends(get_memory_service)):
    """텍스트 및 메타데이터를 벡터로 변환 후 DB에 삽입 (유저별 컬렉션 지원)"""
    collection_name = get_user_collection(req.user_id)
    return service.insert(req, collection_name=collection_name)

@router.post("/search", response_model=List[SearchResult])
def search(req: SearchRequest, service: MemoryService = Depends(get_memory_service)):
    """검색 요청 처리 (유저별 컬렉션 지원)"""
    collection_name = get_user_collection(req.user_id)
    return service.search(req, collection_name=collection_name)

@router.post("/reset_collection")
def reset_collection(req: InsertRequest, service: MemoryService = Depends(get_memory_service)):
    """Qdrant 컬렉션을 삭제 후 재생성하는 엔드포인트 (유저별 컬렉션 지원)"""
    collection_name = get_user_collection(req.user_id)
    try:
        service.reset_collection(collection_name=collection_name)
        return {"status": "ok", "message": f"컬렉션({collection_name})이 성공적으로 초기화되었습니다."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/time")
def get_current_time():
    """현재 서버 시간을 ISO 형식으로 반환"""
    return {"current_time": datetime.now(timezone.utc).isoformat()}

@router.post("/stats")
def get_collection_stats(req: InsertRequest, service: MemoryService = Depends(get_memory_service)):
    """컬렉션의 통계 정보를 반환 (유저별 컬렉션 지원)"""
    collection_name = get_user_collection(req.user_id)
    try:
        collection_info = service.get_collection_stats(collection_name=collection_name)
        return {
            "collection_name": collection_name,
            "vector_count": collection_info.points_count,
            "vector_size": collection_info.config.params.vectors.size,
            "distance": collection_info.config.params.vectors.distance.value
        }
    except Exception as e:
        return {"error": str(e)} 