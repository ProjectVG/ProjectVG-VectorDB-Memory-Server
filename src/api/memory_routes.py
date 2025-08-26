from fastapi import APIRouter, Depends, Header, Query, HTTPException
from typing import List, Dict, Any
from datetime import datetime, timezone

from src.config.settings import MemoryType
from src.models.memory_models import (
    MemoryInsertRequest, MemoryInsertResponse, MemorySearchResult, 
    MultiCollectionSearchResponse
)
from src.service.memory_facade import MemoryFacadeService

router = APIRouter(
    prefix="/api", 
    tags=["Memory API V2 (Refactored)"],
    responses={
        400: {"description": "잘못된 요청"},
        404: {"description": "리소스를 찾을 수 없음"},
        500: {"description": "서버 내부 오류"}
    }
)

_memory_facade = None

def get_memory_facade() -> MemoryFacadeService:
    """메모리 Facade 의존성 (싱글톤)"""
    global _memory_facade
    if _memory_facade is None:
        _memory_facade = MemoryFacadeService()
    return _memory_facade


@router.post(
    "/memory/{memory_type}", 
    response_model=MemoryInsertResponse,
    summary="특정 타입으로 메모리 삽입",
    description="""
    지정된 메모리 타입(Episodic 또는 Semantic)으로 메모리를 삽입합니다.
    
    **Episodic Memory**: 개인 경험, 대화, 감정이 포함된 시간 중심 기억
    **Semantic Memory**: 사실, 지식, 개인 프로필 등 시간에 독립적인 기억
    """
)
async def insert_memory_by_type(
    memory_type: MemoryType,
    request: MemoryInsertRequest,
    facade: MemoryFacadeService = Depends(get_memory_facade)
):
    """특정 타입으로 메모리 삽입 - 비즈니스 로직은 Service에 위임"""
    try:
        # 요청 검증 (HTTP 레벨)
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="텍스트가 비어있습니다.")
        if not request.user_id.strip():
            raise HTTPException(status_code=400, detail="사용자 ID가 비어있습니다.")
        
        # 비즈니스 로직은 Service에 완전히 위임
        result = facade.insert_memory_with_manual_type(
            text=request.text,
            user_id=request.user_id, 
            memory_type=memory_type,
            metadata=_build_metadata_from_request(request)
        )
        
        # HTTP 응답 변환
        return MemoryInsertResponse(
            id=result["id"],
            memory_type=MemoryType(result["memory_type"]),
            collection_name=result["memory_type"],
            user_id=request.user_id,
            timestamp=result.get("timestamp") or datetime.now(timezone.utc).isoformat()
        )
        
    except HTTPException:
        raise  # HTTP 예외는 그대로 전달
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"메모리 삽입 실패: {str(e)}")


@router.post(
    "/memory", 
    response_model=MemoryInsertResponse,
    summary="AI 자동 분류로 메모리 삽입",
    description="""
    AI가 텍스트 내용을 분석하여 자동으로 메모리 타입을 결정하고 삽입합니다.
    분류 신뢰도와 설명을 응답에 포함합니다.
    """
)
async def insert_memory_auto_classify(
    request: MemoryInsertRequest,
    facade: MemoryFacadeService = Depends(get_memory_facade)
):
    """AI 자동 분류로 메모리 삽입 - 비즈니스 로직은 Service에 위임"""
    try:
        # HTTP 요청 검증
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="텍스트가 비어있습니다.")
        if not request.user_id.strip():
            raise HTTPException(status_code=400, detail="사용자 ID가 비어있습니다.")
        
        # 모든 비즈니스 로직을 Service에 위임
        result = facade.insert_memory_with_auto_classification(
            text=request.text,
            user_id=request.user_id,
            metadata=_build_metadata_from_request(request)
        )
        
        # HTTP 응답 변환
        return MemoryInsertResponse(
            id=result["id"],
            memory_type=MemoryType(result["memory_type"]),
            collection_name=result["memory_type"],
            user_id=request.user_id,
            timestamp=result.get("timestamp"),
            classification_confidence=result.get("confidence"),
            classification_explanation=result.get("explanation")
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"메모리 삽입 실패: {str(e)}")


@router.get("/memory/{memory_type}/search", response_model=List[MemorySearchResult])
async def search_memory_by_type(
    memory_type: MemoryType,
    query: str,
    user_id: str = Header(..., alias="X-User-ID"),
    limit: int = Query(default=10, ge=1, le=100),
    similarity_threshold: float = Query(default=0.0, ge=0.0, le=1.0),
    facade: MemoryFacadeService = Depends(get_memory_facade)
):
    """단일 컬렉션 검색 - 비즈니스 로직은 Service에 위임"""
    try:
        # HTTP 요청 검증
        if not query.strip():
            raise HTTPException(status_code=400, detail="검색 쿼리가 비어있습니다.")
        if not user_id.strip():
            raise HTTPException(status_code=400, detail="사용자 ID 헤더가 필요합니다.")
        
        # 검색 필터 구성 (HTTP 파라미터 → 비즈니스 로직 파라미터)
        filters = {}
        if similarity_threshold > 0:
            filters["min_score"] = similarity_threshold
        
        # 비즈니스 로직은 Service에 위임
        results = facade.search_memory_single_collection(
            query=query,
            user_id=user_id,
            memory_type=memory_type,
            limit=limit,
            filters=filters
        )
        
        # 비즈니스 객체 → HTTP 응답 변환
        return [_convert_memory_point_to_search_result(result, memory_type) for result in results]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검색 실패: {str(e)}")


@router.get("/memory/search/multi", response_model=MultiCollectionSearchResponse)
async def multi_collection_search(
    query: str,
    user_id: str = Header(..., alias="X-User-ID"),
    collections: List[MemoryType] = Query(default=[MemoryType.EPISODIC, MemoryType.SEMANTIC]),
    limit: int = Query(default=10, ge=1, le=100),
    episodic_weight: float = Query(default=1.0, ge=0.0, le=2.0),
    semantic_weight: float = Query(default=1.0, ge=0.0, le=2.0),
    use_intelligent_weights: bool = Query(default=False),
    facade: MemoryFacadeService = Depends(get_memory_facade)
):
    """다중 컬렉션 통합 검색 - 지능형 가중치 옵션 포함"""
    try:
        # HTTP 요청 검증
        if not query.strip():
            raise HTTPException(status_code=400, detail="검색 쿼리가 비어있습니다.")
        if not user_id.strip():
            raise HTTPException(status_code=400, detail="사용자 ID 헤더가 필요합니다.")
        
        # 비즈니스 로직 선택: 지능형 가중치 vs 수동 가중치
        if use_intelligent_weights:
            result = facade.search_memory_intelligent(query, user_id, limit)
            search_results = result["results"]
            applied_weights = result.get("applied_weights", {})
            explanation = result.get("explanation", "")
        else:
            # 수동 가중치 설정
            weights = {
                MemoryType.EPISODIC: episodic_weight,
                MemoryType.SEMANTIC: semantic_weight
            }
            search_results = facade.search_memory_multi_collection(
                query, user_id, collections, limit, weights
            )
            applied_weights = {k.value: v for k, v in weights.items()}
            explanation = "수동 가중치 적용"
        
        # 응답 통계 계산
        collection_stats = {}
        for result in search_results:
            collection_type = getattr(result, 'collection_type', result.memory_type.value if hasattr(result, 'memory_type') else 'unknown')
            collection_stats[collection_type] = collection_stats.get(collection_type, 0) + 1
        
        # HTTP 응답 구성
        return MultiCollectionSearchResponse(
            results=[_convert_memory_point_to_search_result(r) for r in search_results],
            collection_stats=collection_stats,
            total_results=len(search_results),
            query_time_ms=0.0,  # Service에서 측정하도록 개선 가능
            user_id=user_id,
            query=query,
            applied_weights=applied_weights,
            explanation=explanation
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"다중 컬렉션 검색 실패: {str(e)}")



def _build_metadata_from_request(request: MemoryInsertRequest) -> Dict[str, Any]:
    """HTTP 요청을 비즈니스 로직용 메타데이터로 변환"""
    metadata = {}
    
    # 공통 필드
    if request.importance_score is not None:
        metadata["importance_score"] = request.importance_score
    if request.source:
        metadata["source"] = request.source
    if request.timestamp:
        metadata["timestamp"] = request.timestamp
    
    # Episodic 필드
    if request.speaker:
        metadata["speaker"] = request.speaker
    if request.emotion:
        metadata["emotion"] = request.emotion
    if request.context:
        metadata["context"] = request.context
    if request.links:
        metadata["links"] = request.links
    
    # Semantic 필드
    if request.fact_type:
        metadata["fact_type"] = request.fact_type
    if request.confidence_score is not None:
        metadata["confidence_score"] = request.confidence_score
    
    return metadata


def _convert_memory_point_to_search_result(memory_point, memory_type=None) -> MemorySearchResult:
    """비즈니스 객체를 HTTP 응답 객체로 변환"""
    # memory_point의 실제 구조에 따라 구현
    # 이는 MemoryPoint 모델의 정확한 구조를 알아야 함
    
    # 메모리 타입 결정
    if memory_type is None:
        memory_type = getattr(memory_point, 'memory_type', MemoryType.SEMANTIC)
    
    # 타입별 특화 데이터 추출
    episodic_data = None
    semantic_data = None
    
    if hasattr(memory_point, 'metadata'):
        metadata = memory_point.metadata
        
        if memory_type == MemoryType.EPISODIC:
            episodic_data = {
                "speaker": metadata.get("speaker"),
                "emotion": metadata.get("emotion"),
                "context": metadata.get("context"),
                "links": metadata.get("links")
            }
        elif memory_type == MemoryType.SEMANTIC:
            semantic_data = {
                "fact_type": metadata.get("fact_type"),
                "confidence_score": metadata.get("confidence_score"),
                "last_updated": metadata.get("last_updated")
            }
    
    return MemorySearchResult(
        id=str(getattr(memory_point, 'id', '')),
        text=getattr(memory_point, 'text', ''),
        memory_type=memory_type,
        collection_name=memory_type.value,
        score=getattr(memory_point, 'score', 0.0),
        user_id=getattr(memory_point, 'user_id', ''),
        timestamp=getattr(memory_point, 'timestamp', None),
        importance_score=getattr(memory_point, 'importance_score', 0.5),
        source=getattr(memory_point, 'source', ''),
        episodic_data=episodic_data,
        semantic_data=semantic_data
    )