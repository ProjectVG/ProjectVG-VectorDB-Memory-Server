"""
시스템 관리 API 라우터
- 컬렉션 관리 (초기화, 통계)
- 시스템 전체 통계
- 관리자 전용 기능
"""
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone

from src.config.settings import MemoryType
from src.models.memory_models import SystemStats
from src.service.memory_facade import MemoryFacadeService

router = APIRouter(
    prefix="/api/admin", 
    tags=["System Administration"],
    responses={
        400: {"description": "잘못된 요청"},
        403: {"description": "권한 없음"},
        500: {"description": "서버 내부 오류"}
    }
)

# 의존성 주입 - 싱글톤 패턴
_memory_facade = None

def get_memory_facade() -> MemoryFacadeService:
    """메모리 Facade 의존성 (싱글톤)"""
    global _memory_facade
    if _memory_facade is None:
        _memory_facade = MemoryFacadeService()
    return _memory_facade


@router.post("/collections/{memory_type}/reset")
async def reset_collection(
    memory_type: MemoryType,
    facade: MemoryFacadeService = Depends(get_memory_facade)
):
    """컬렉션 초기화 - 비즈니스 로직은 Facade에 위임"""
    try:
        # 비즈니스 로직은 Facade에 위임
        result = facade.reset_collection(memory_type)
        
        if result.get("reset_success", False):
            return {
                "status": "success",
                "message": f"컬렉션 {memory_type.value}이 초기화되었습니다.",
                "timestamp": result.get("timestamp")
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "초기화 실패"))
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"컬렉션 초기화 실패: {str(e)}")


@router.get("/collections/{memory_type}/stats")
async def get_collection_stats(
    memory_type: MemoryType,
    facade: MemoryFacadeService = Depends(get_memory_facade)
):
    """컬렉션 통계 정보 조회"""
    try:
        # 비즈니스 로직은 Facade에 위임
        stats = facade.get_collection_stats(memory_type)
        
        if "error" in stats:
            raise HTTPException(status_code=500, detail=stats["error"])
        
        return {
            "collection_name": stats["collection_name"],
            "memory_type": stats["memory_type"],
            "total_points": stats["total_points"],
            "vector_size": stats["vector_size"],
            "distance_function": stats["distance_function"],
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"컬렉션 통계 조회 실패: {str(e)}")


@router.get("/system/stats", response_model=SystemStats)
async def get_system_stats(
    facade: MemoryFacadeService = Depends(get_memory_facade)
):
    """시스템 전체 통계 - Facade로 위임하되 기존 로직 유지"""
    try:
        # 각 컬렉션의 통계 수집
        collections_info = []
        total_memories = 0
        
        for memory_type in [MemoryType.EPISODIC, MemoryType.SEMANTIC]:
            try:
                stats = facade.get_collection_stats(memory_type)
                
                if "error" not in stats:
                    total_points = stats["total_points"]
                    total_memories += total_points
                    
                    collections_info.append({
                        "name": stats["collection_name"],
                        "memory_type": memory_type,
                        "vector_dim": stats["vector_size"],
                        "distance": stats["distance_function"],
                        "total_points": total_points,
                        "user_count": 0,  # 실제 구현에서는 사용자 수 계산 필요
                        "avg_points_per_user": 0.0
                    })
                else:
                    # 컬렉션이 없거나 오류 시 기본값
                    collections_info.append({
                        "name": memory_type.value,
                        "memory_type": memory_type,
                        "vector_dim": 1536,
                        "distance": "COSINE",
                        "total_points": 0,
                        "user_count": 0,
                        "avg_points_per_user": 0.0
                    })
                    
            except Exception:
                # 오류 시 기본값
                collections_info.append({
                    "name": memory_type.value,
                    "memory_type": memory_type,
                    "vector_dim": 1536,
                    "distance": "COSINE",
                    "total_points": 0,
                    "user_count": 0,
                    "avg_points_per_user": 0.0
                })
        
        return SystemStats(
            total_collections=len(collections_info),
            total_users=0,  # 실제 구현에서는 전체 사용자 수 계산 필요
            total_memories=total_memories,
            collections=collections_info,
            avg_query_time_ms=50.0,  # 기본값 (실제 측정 필요)
            classification_accuracy=None,
            uptime_hours=0.0,  # 실제 업타임 계산 필요
            last_updated=datetime.now(timezone.utc).isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시스템 통계 조회 실패: {str(e)}")


@router.get("/health/detailed")
async def get_detailed_health_check(
    facade: MemoryFacadeService = Depends(get_memory_facade)
):
    """상세한 시스템 건강 상태 체크"""
    try:
        health_status = {
            "overall_status": "healthy",
            "components": {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # 각 컬렉션 건강 상태 체크
        for memory_type in [MemoryType.EPISODIC, MemoryType.SEMANTIC]:
            try:
                stats = facade.get_collection_stats(memory_type)
                
                if "error" not in stats:
                    health_status["components"][memory_type.value] = {
                        "status": "healthy",
                        "total_points": stats["total_points"],
                        "vector_size": stats["vector_size"],
                        "message": f"컬렉션 {memory_type.value}이 정상 작동 중"
                    }
                else:
                    health_status["components"][memory_type.value] = {
                        "status": "unhealthy",
                        "error": stats["error"],
                        "message": f"컬렉션 {memory_type.value}에 문제 발생"
                    }
                    health_status["overall_status"] = "degraded"
                    
            except Exception as e:
                health_status["components"][memory_type.value] = {
                    "status": "error",
                    "error": str(e),
                    "message": f"컬렉션 {memory_type.value} 상태 확인 실패"
                }
                health_status["overall_status"] = "unhealthy"
        
        # 임베딩 서비스 건강 상태 체크
        try:
            # 간단한 임베딩 테스트
            test_result = facade.classify_memory("테스트 텍스트")
            health_status["components"]["embedding_service"] = {
                "status": "healthy",
                "confidence": test_result["confidence"],
                "message": "임베딩 서비스가 정상 작동 중"
            }
        except Exception as e:
            health_status["components"]["embedding_service"] = {
                "status": "error",
                "error": str(e),
                "message": "임베딩 서비스 오류"
            }
            health_status["overall_status"] = "unhealthy"
        
        # 분류 서비스 건강 상태 체크
        try:
            threshold = facade.classification_service.get_classification_confidence_threshold()
            health_status["components"]["classification_service"] = {
                "status": "healthy",
                "confidence_threshold": threshold,
                "message": "분류 서비스가 정상 작동 중"
            }
        except Exception as e:
            health_status["components"]["classification_service"] = {
                "status": "error",
                "error": str(e),
                "message": "분류 서비스 오류"
            }
            health_status["overall_status"] = "unhealthy"
        
        return health_status
        
    except Exception as e:
        return {
            "overall_status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@router.post("/maintenance/optimize")
async def optimize_system(
    facade: MemoryFacadeService = Depends(get_memory_facade)
):
    """시스템 최적화 작업 수행"""
    try:
        optimization_results = {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "tasks": [],
            "overall_status": "success"
        }
        
        # 각 컬렉션에 대해 최적화 작업 수행
        for memory_type in [MemoryType.EPISODIC, MemoryType.SEMANTIC]:
            try:
                stats_before = facade.get_collection_stats(memory_type)
                
                # 여기서 실제 최적화 작업 수행 (예: 인덱스 재구성, 압축 등)
                # 현재는 시뮬레이션
                
                stats_after = facade.get_collection_stats(memory_type)
                
                optimization_results["tasks"].append({
                    "task": f"optimize_collection_{memory_type.value}",
                    "status": "completed",
                    "points_before": stats_before.get("total_points", 0),
                    "points_after": stats_after.get("total_points", 0),
                    "message": f"컬렉션 {memory_type.value} 최적화 완료"
                })
                
            except Exception as e:
                optimization_results["tasks"].append({
                    "task": f"optimize_collection_{memory_type.value}",
                    "status": "failed",
                    "error": str(e),
                    "message": f"컬렉션 {memory_type.value} 최적화 실패"
                })
                optimization_results["overall_status"] = "partial_success"
        
        optimization_results["completed_at"] = datetime.now(timezone.utc).isoformat()
        return optimization_results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시스템 최적화 실패: {str(e)}")


@router.get("/config/current")
async def get_current_configuration():
    """현재 시스템 설정 정보 조회"""
    try:
        from src.config.settings import (
            server_config, db_config, openai_embedding_config, collection_config
        )
        
        return {
            "server": {
                "host": server_config.server_host,
                "port": server_config.server_port
            },
            "database": {
                "qdrant_host": db_config.qdrant_host,
                "qdrant_port": db_config.qdrant_port,
                "vector_dim": db_config.vector_dim
            },
            "embedding": {
                "model_name": openai_embedding_config.openai_model_name,
                "vector_dimension": openai_embedding_config.vector_dimension,
                "has_api_key": bool(openai_embedding_config.openai_api_key)
            },
            "collections": {
                "episodic_vector_dim": collection_config.episodic_vector_dim,
                "semantic_vector_dim": collection_config.semantic_vector_dim,
                "auto_create_collections": collection_config.auto_create_collections
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"설정 조회 실패: {str(e)}")