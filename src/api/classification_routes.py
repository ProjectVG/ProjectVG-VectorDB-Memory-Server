"""
분류 및 분석 API 라우터
- 텍스트 메모리 타입 분류
- 분류 설명 및 신뢰도 제공
- 배치 분류 기능
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional, Dict, Any

from src.models.memory_models import ClassificationResult
from src.service.memory_facade import MemoryFacadeService

router = APIRouter(
    prefix="/api/classify", 
    tags=["Classification & Analysis"],
    responses={
        400: {"description": "잘못된 요청"},
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


@router.post("/", response_model=ClassificationResult)
async def classify_text(
    text: str,
    context: Optional[Dict[str, Any]] = None,
    facade: MemoryFacadeService = Depends(get_memory_facade)
):
    """텍스트 메모리 타입 분류 - 비즈니스 로직은 Facade에 위임"""
    try:
        if not text.strip():
            raise HTTPException(status_code=400, detail="분류할 텍스트가 비어있습니다.")
        
        # 비즈니스 로직은 Facade에 위임
        classification = facade.classify_memory(text, context or {})
        
        # HTTP 응답 변환
        return ClassificationResult(
            predicted_type=classification["predicted_type"],
            confidence=classification["confidence"],
            explanation=classification["explanation"],
            episodic_score=classification.get("episodic_score", 0.0),
            semantic_score=classification.get("semantic_score", 0.0),
            features=classification.get("features", {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분류 실패: {str(e)}")


@router.post("/batch")
async def batch_classify_texts(
    texts: List[str],
    contexts: Optional[List[Dict[str, Any]]] = None,
    facade: MemoryFacadeService = Depends(get_memory_facade)
):
    """배치 텍스트 분류"""
    try:
        if not texts:
            raise HTTPException(status_code=400, detail="분류할 텍스트 목록이 비어있습니다.")
        
        if any(not text.strip() for text in texts):
            raise HTTPException(status_code=400, detail="비어있는 텍스트가 포함되어 있습니다.")
        
        # 비즈니스 로직은 Facade에 위임
        classifications = facade.batch_classify_memories(texts, contexts)
        
        # 결과 통계 계산
        total_count = len(classifications)
        episodic_count = sum(1 for c in classifications if c["predicted_type"].value == "episodic")
        semantic_count = total_count - episodic_count
        
        high_confidence_count = sum(1 for c in classifications if c["confidence"] >= 0.8)
        low_confidence_count = sum(1 for c in classifications if c["confidence"] < 0.6)
        
        return {
            "classifications": [
                {
                    "text": texts[i],
                    "predicted_type": c["predicted_type"].value,
                    "confidence": c["confidence"],
                    "explanation": c["explanation"],
                    "features": c.get("features", {})
                }
                for i, c in enumerate(classifications)
            ],
            "statistics": {
                "total_texts": total_count,
                "episodic_count": episodic_count,
                "semantic_count": semantic_count,
                "episodic_ratio": episodic_count / total_count,
                "semantic_ratio": semantic_count / total_count,
                "high_confidence_count": high_confidence_count,
                "low_confidence_count": low_confidence_count,
                "avg_confidence": sum(c["confidence"] for c in classifications) / total_count
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"배치 분류 실패: {str(e)}")


@router.get("/confidence-threshold")
async def get_classification_confidence_threshold(
    facade: MemoryFacadeService = Depends(get_memory_facade)
):
    """현재 분류 신뢰도 임계값 조회"""
    try:
        # Facade의 분류 서비스에서 임계값 가져오기
        threshold = facade.classification_service.get_classification_confidence_threshold()
        
        return {
            "confidence_threshold": threshold,
            "description": f"신뢰도 {threshold} 이상에서 자동 분류를 신뢰할 수 있습니다.",
            "recommendation": f"신뢰도가 {threshold} 미만인 경우 수동 분류를 고려하세요."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"임계값 조회 실패: {str(e)}")


@router.post("/analyze-patterns")
async def analyze_classification_patterns(
    texts: List[str],
    facade: MemoryFacadeService = Depends(get_memory_facade)
):
    """텍스트 패턴 분석 및 분류 특성 추출"""
    try:
        if not texts:
            raise HTTPException(status_code=400, detail="분석할 텍스트 목록이 비어있습니다.")
        
        # 배치 분류 실행
        classifications = facade.batch_classify_memories(texts)
        
        # 패턴 분석
        episodic_features = []
        semantic_features = []
        
        for i, classification in enumerate(classifications):
            features = classification.get("features", {})
            if classification["predicted_type"].value == "episodic":
                episodic_features.append(features)
            else:
                semantic_features.append(features)
        
        # 특성 통계 계산
        def calculate_feature_stats(feature_list):
            if not feature_list:
                return {}
            
            feature_names = ["temporal_matches", "emotional_matches", "conversation_matches", 
                           "factual_matches", "profile_matches"]
            
            stats = {}
            for feature_name in feature_names:
                values = [f.get(feature_name, 0) for f in feature_list]
                if values:
                    stats[feature_name] = {
                        "avg": sum(values) / len(values),
                        "max": max(values),
                        "min": min(values),
                        "total_occurrences": sum(1 for v in values if v > 0)
                    }
            return stats
        
        episodic_stats = calculate_feature_stats(episodic_features)
        semantic_stats = calculate_feature_stats(semantic_features)
        
        # 주요 패턴 추출
        patterns = []
        
        if episodic_stats.get("emotional_matches", {}).get("avg", 0) > 1:
            patterns.append("Episodic 텍스트에서 강한 감정 표현이 자주 나타남")
        
        if episodic_stats.get("temporal_matches", {}).get("avg", 0) > 1:
            patterns.append("Episodic 텍스트에서 시간 표현이 빈번하게 사용됨")
        
        if semantic_stats.get("factual_matches", {}).get("avg", 0) > 1:
            patterns.append("Semantic 텍스트에서 사실적 표현이 주로 나타남")
        
        if semantic_stats.get("profile_matches", {}).get("avg", 0) > 1:
            patterns.append("Semantic 텍스트에서 개인 프로필 정보가 자주 포함됨")
        
        return {
            "total_texts_analyzed": len(texts),
            "episodic_count": len(episodic_features),
            "semantic_count": len(semantic_features),
            "episodic_feature_stats": episodic_stats,
            "semantic_feature_stats": semantic_stats,
            "identified_patterns": patterns,
            "recommendations": [
                "감정 표현이 많은 텍스트는 Episodic으로 분류될 가능성이 높습니다.",
                "시간 정보가 포함된 텍스트는 대부분 Episodic 메모리입니다.",
                "사실적 정보나 개인 프로필 데이터는 Semantic 메모리로 분류됩니다."
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"패턴 분석 실패: {str(e)}")


@router.post("/validate-classification")
async def validate_classification_decision(
    text: str,
    expected_type: str,
    facade: MemoryFacadeService = Depends(get_memory_facade)
):
    """분류 결정 검증 및 개선 제안"""
    try:
        if not text.strip():
            raise HTTPException(status_code=400, detail="검증할 텍스트가 비어있습니다.")
        
        if expected_type not in ["episodic", "semantic"]:
            raise HTTPException(status_code=400, detail="expected_type은 'episodic' 또는 'semantic'이어야 합니다.")
        
        # 현재 분류 수행
        classification = facade.classify_memory(text)
        predicted_type = classification["predicted_type"].value
        confidence = classification["confidence"]
        
        # 검증 결과 계산
        is_correct = predicted_type == expected_type
        confidence_level = "high" if confidence >= 0.8 else "medium" if confidence >= 0.6 else "low"
        
        # 개선 제안 생성
        suggestions = []
        if not is_correct:
            suggestions.append(f"분류기가 '{predicted_type}'으로 예측했지만 실제는 '{expected_type}'입니다.")
            
            if confidence >= 0.7:
                suggestions.append("높은 신뢰도로 잘못 분류되었습니다. 분류 규칙 개선이 필요할 수 있습니다.")
            else:
                suggestions.append("낮은 신뢰도로 분류되었습니다. 추가 컨텍스트 정보가 도움될 수 있습니다.")
        
        if confidence < 0.6:
            suggestions.append("분류 신뢰도가 낮습니다. 텍스트에 더 명확한 단서가 필요할 수 있습니다.")
        
        return {
            "text": text,
            "predicted_type": predicted_type,
            "expected_type": expected_type,
            "is_correct": is_correct,
            "confidence": confidence,
            "confidence_level": confidence_level,
            "explanation": classification["explanation"],
            "features": classification.get("features", {}),
            "suggestions": suggestions,
            "validation_result": "PASS" if is_correct else "FAIL"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검증 실패: {str(e)}")