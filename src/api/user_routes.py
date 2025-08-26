"""
사용자 관리 API 라우터
- 사용자별 통계 조회
- 사용자 메모리 관리 (삭제 등)
- 사용자 프로필 관련 기능
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional

from src.config.settings import MemoryType
from src.models.memory_models import UserMemoryStats
from src.service.memory_facade import MemoryFacadeService

router = APIRouter(
    prefix="/api/users", 
    tags=["User Management"],
    responses={
        400: {"description": "잘못된 요청"},
        404: {"description": "사용자를 찾을 수 없음"},
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


@router.get("/{user_id}/stats", response_model=UserMemoryStats)
async def get_user_memory_stats(
    user_id: str,
    facade: MemoryFacadeService = Depends(get_memory_facade)
):
    """사용자 메모리 통계 조회 - 비즈니스 로직은 Facade에 위임"""
    try:
        if not user_id.strip():
            raise HTTPException(status_code=400, detail="사용자 ID가 필요합니다.")
        
        # 비즈니스 로직은 Facade에 위임
        stats = facade.get_user_memory_summary(user_id)
        
        # HTTP 응답 변환
        return UserMemoryStats(
            user_id=user_id,
            total_memories=stats["total_memories"],
            episodic_count=stats["episodic_count"],
            semantic_count=stats["semantic_count"],
            # 추가 통계는 Service에서 계산하도록 개선 가능
            oldest_memory=None,
            newest_memory=None,
            daily_average=0.0,
            most_active_day=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 조회 실패: {str(e)}")


@router.delete("/{user_id}/memories")
async def delete_user_memories(
    user_id: str,
    memory_type: Optional[MemoryType] = Query(default=None),
    facade: MemoryFacadeService = Depends(get_memory_facade)
):
    """사용자 메모리 삭제 - 비즈니스 로직은 Facade에 위임"""
    try:
        if not user_id.strip():
            raise HTTPException(status_code=400, detail="사용자 ID가 필요합니다.")
        
        # 비즈니스 로직은 Facade에 위임
        result = facade.delete_user_memories(user_id, memory_type)
        
        if result.get("success", True):
            type_msg = f" ({memory_type.value})" if memory_type else " (전체)"
            return {
                "status": "success",
                "message": f"사용자 {user_id}의 메모리{type_msg}가 삭제되었습니다.",
                "deleted_count": result.get("deleted_count", 0)
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "삭제 실패"))
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"메모리 삭제 실패: {str(e)}")


@router.get("/{user_id}/profile")
async def get_user_profile(
    user_id: str,
    facade: MemoryFacadeService = Depends(get_memory_facade)
):
    """사용자 프로필 정보 조회 (Semantic 메모리에서 추출)"""
    try:
        if not user_id.strip():
            raise HTTPException(status_code=400, detail="사용자 ID가 필요합니다.")
        
        # 프로필 관련 검색
        profile_results = facade.search_memory_single_collection(
            query="생일 나이 직업 취미 이름",  # 프로필 키워드로 검색
            user_id=user_id,
            memory_type=MemoryType.SEMANTIC,
            limit=20
        )
        
        # 프로필 데이터 추출
        profile_data = {}
        for result in profile_results:
            if hasattr(result, 'metadata'):
                text = result.metadata.get("text", "")
                # 간단한 키워드 매칭으로 프로필 정보 추출
                if any(keyword in text for keyword in ["생일", "태어났", "출생"]):
                    profile_data["birthday"] = text
                elif any(keyword in text for keyword in ["직업", "일하", "근무"]):
                    profile_data["occupation"] = text
                elif any(keyword in text for keyword in ["취미", "좋아하", "관심"]):
                    profile_data["interests"] = text
                elif any(keyword in text for keyword in ["이름", "불러", "부르"]):
                    profile_data["name"] = text
        
        return {
            "user_id": user_id,
            "profile": profile_data,
            "profile_completeness": len(profile_data) / 4.0,  # 4개 카테고리 기준
            "last_updated": None  # 실제 구현에서는 최신 업데이트 시간 계산
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"프로필 조회 실패: {str(e)}")


@router.get("/{user_id}/classification-analysis")
async def get_user_classification_analysis(
    user_id: str,
    facade: MemoryFacadeService = Depends(get_memory_facade)
):
    """사용자의 메모리 분류 패턴 분석"""
    try:
        if not user_id.strip():
            raise HTTPException(status_code=400, detail="사용자 ID가 필요합니다.")
        
        # 사용자 메모리 통계 가져오기
        stats = facade.get_user_memory_summary(user_id)
        
        total_memories = stats["total_memories"]
        if total_memories == 0:
            return {
                "user_id": user_id,
                "analysis": "분석할 메모리가 없습니다.",
                "recommendations": ["메모리를 추가한 후 분석을 시도해보세요."]
            }
        
        # 분류 패턴 분석
        episodic_ratio = stats["memory_distribution"]["episodic_ratio"]
        semantic_ratio = stats["memory_distribution"]["semantic_ratio"]
        
        analysis = []
        recommendations = []
        
        if episodic_ratio > 0.7:
            analysis.append("주로 개인 경험과 대화 중심의 기억을 저장합니다.")
            recommendations.append("지식이나 사실 정보도 함께 저장하면 더 균형잡힌 메모리 관리가 가능합니다.")
        elif semantic_ratio > 0.7:
            analysis.append("주로 사실과 지식 중심의 정보를 저장합니다.")
            recommendations.append("개인 경험과 감정이 담긴 기억도 함께 저장하면 더 풍부한 기억 관리가 가능합니다.")
        else:
            analysis.append("Episodic과 Semantic 메모리가 균형있게 분포되어 있습니다.")
            recommendations.append("현재의 균형잡힌 메모리 패턴을 유지하세요.")
        
        return {
            "user_id": user_id,
            "total_memories": total_memories,
            "episodic_ratio": round(episodic_ratio, 3),
            "semantic_ratio": round(semantic_ratio, 3),
            "analysis": " ".join(analysis),
            "recommendations": recommendations,
            "memory_type_preference": "episodic" if episodic_ratio > semantic_ratio else "semantic"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분류 분석 실패: {str(e)}")