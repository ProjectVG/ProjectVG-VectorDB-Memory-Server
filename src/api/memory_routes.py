from fastapi import APIRouter, Depends, Header, Query, HTTPException
from typing import List, Optional, Dict, Any
import time
from datetime import datetime, timezone

from src.config.settings import MemoryType
from src.models.memory_models import (
    MemoryInsertRequest, MemoryInsertResponse, MemorySearchResult, 
    MultiCollectionSearchResponse, ClassificationResult, UserMemoryStats, SystemStats
)
from src.repository.memory_repository import MemoryQdrantRepository
from src.service.memory_classifier import MemoryClassifier
from src.infra.embedding import EmbeddingService
from src.config.settings import EmbeddingType, embedding_config, openai_embedding_config

router = APIRouter(
    prefix="/api", 
    tags=["Memory API"],
    responses={
        400: {"description": "잘못된 요청"},
        404: {"description": "리소스를 찾을 수 없음"},
        500: {"description": "서버 내부 오류"}
    }
)

def get_memory_repository():
    """메모리 Repository 의존성"""
    return MemoryQdrantRepository()

def get_memory_classifier():
    """메모리 분류기 의존성"""
    return MemoryClassifier()

def get_embedding_service() -> EmbeddingService:
    """임베딩 서비스 의존성 (OpenAI만 지원)"""
    from src.infra.embedding import OpenAIEmbeddingService
    return OpenAIEmbeddingService(
        api_key=openai_embedding_config.openai_api_key,
        model_name=openai_embedding_config.openai_model_name,
        dimensions=openai_embedding_config.vector_dimension if openai_embedding_config.vector_dimension != 1536 else None,
        user_identifier=openai_embedding_config.user_identifier if openai_embedding_config.user_identifier else None
    )

@router.post(
    "/memory/{memory_type}", 
    response_model=MemoryInsertResponse,
    summary="특정 타입으로 메모리 삽입",
    description="""
    지정된 메모리 타입(Episodic 또는 Semantic)으로 메모리를 삽입합니다.
    
    **Episodic Memory**: 개인 경험, 대화, 감정이 포함된 시간 중심 기억
    - speaker, emotion, context, links 필드 활용
    
    **Semantic Memory**: 사실, 지식, 개인 프로필 등 시간에 독립적인 기억  
    - fact_type, confidence_score 필드 활용
    """,
    responses={
        200: {
            "description": "메모리가 성공적으로 삽입됨",
            "content": {
                "application/json": {
                    "example": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "memory_type": "episodic",
                        "collection_name": "episodic",
                        "user_id": "user123",
                        "timestamp": "2025-08-26T07:15:00Z"
                    }
                }
            }
        }
    }
)
async def insert_memory_by_type(
    memory_type: MemoryType,
    request: MemoryInsertRequest,
    repository: MemoryQdrantRepository = Depends(get_memory_repository),
    embedding_service = Depends(get_embedding_service)
):
    try:
        # 임베딩 생성
        embedding = embedding_service.encode(request.text)
        
        # 메모리 데이터 구성
        memory_data = {
            "text": request.text,
            "embedding": embedding,
            "timestamp": request.timestamp or datetime.now(timezone.utc).isoformat(),
            "importance_score": request.importance_score,
            "source": request.source
        }
        
        # 메모리 타입에 따른 특화 데이터 추가
        if memory_type == MemoryType.EPISODIC:
            if request.speaker:
                memory_data["speaker"] = request.speaker
            if request.emotion:
                memory_data["emotion"] = request.emotion
            if request.context:
                memory_data["context"] = request.context
            if request.links:
                memory_data["links"] = request.links
        elif memory_type == MemoryType.SEMANTIC:
            if request.fact_type:
                memory_data["fact_type"] = request.fact_type
            memory_data["confidence_score"] = request.confidence_score
            memory_data["last_updated"] = datetime.now(timezone.utc).isoformat()
        
        # 메모리 삽입
        memory_id = repository.insert_memory(memory_data, request.user_id, memory_type)
        
        return MemoryInsertResponse(
            id=memory_id,
            memory_type=memory_type,
            collection_name=memory_type.value,
            user_id=request.user_id,
            timestamp=memory_data["timestamp"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"메모리 삽입 실패: {str(e)}")

@router.post(
    "/memory", 
    response_model=MemoryInsertResponse,
    summary="AI 자동 분류로 메모리 삽입",
    description="""
    AI가 텍스트 내용을 분석하여 자동으로 메모리 타입을 결정하고 삽입합니다.
    
    **분류 기준**:
    - **Episodic**: 시간 표현, 감정, 대화, 개인 경험이 포함된 텍스트
    - **Semantic**: 사실, 정의, 지식, 개인 프로필 정보가 포함된 텍스트
    
    분류 신뢰도와 설명을 응답에 포함하여 분류 근거를 확인할 수 있습니다.
    """,
    responses={
        200: {
            "description": "메모리가 자동 분류되어 삽입됨",
            "content": {
                "application/json": {
                    "example": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "memory_type": "episodic", 
                        "collection_name": "episodic",
                        "user_id": "user123",
                        "timestamp": "2025-08-26T07:15:00Z",
                        "classification_confidence": 0.85,
                        "classification_explanation": "episodic 타입으로 분류 (신뢰도: 0.85) - 시간 표현 1개, 감정 표현 1개 감지"
                    }
                }
            }
        }
    }
)
async def insert_memory_auto_classify(
    request: MemoryInsertRequest,
    repository: MemoryQdrantRepository = Depends(get_memory_repository),
    classifier: MemoryClassifier = Depends(get_memory_classifier),
    embedding_service = Depends(get_embedding_service)
):
    try:
        # 메모리 타입 자동 분류
        context = {}
        if request.emotion:
            context["emotion"] = request.emotion
        if request.speaker:
            context["speaker"] = request.speaker
        if request.fact_type:
            context["fact_type"] = request.fact_type
            
        classification = classifier.classify_with_confidence(request.text, context)
        memory_type = classification["predicted_type"]
        
        # 임베딩 생성
        embedding = embedding_service.encode(request.text)
        
        # 메모리 데이터 구성
        memory_data = {
            "text": request.text,
            "embedding": embedding,
            "timestamp": request.timestamp or datetime.now(timezone.utc).isoformat(),
            "importance_score": request.importance_score,
            "source": request.source
        }
        
        # 메모리 타입에 따른 특화 데이터 추가
        if memory_type == MemoryType.EPISODIC:
            if request.speaker:
                memory_data["speaker"] = request.speaker
            if request.emotion:
                memory_data["emotion"] = request.emotion
            if request.context:
                memory_data["context"] = request.context
            if request.links:
                memory_data["links"] = request.links
        elif memory_type == MemoryType.SEMANTIC:
            if request.fact_type:
                memory_data["fact_type"] = request.fact_type
            memory_data["confidence_score"] = request.confidence_score
            memory_data["last_updated"] = datetime.now(timezone.utc).isoformat()
        
        # 메모리 삽입
        memory_id = repository.insert_memory(memory_data, request.user_id, memory_type)
        
        return MemoryInsertResponse(
            id=memory_id,
            memory_type=memory_type,
            collection_name=memory_type.value,
            user_id=request.user_id,
            timestamp=memory_data["timestamp"],
            classification_confidence=classification["confidence"],
            classification_explanation=classifier.get_classification_explanation(request.text, context)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"메모리 삽입 실패: {str(e)}")

@router.get("/memory/{memory_type}/search", response_model=List[MemorySearchResult])
async def search_memory_by_type(
    memory_type: MemoryType,
    query: str,
    user_id: str = Header(..., alias="X-User-ID"),
    limit: int = Query(default=10, ge=1, le=100),
    similarity_threshold: float = Query(default=0.0, ge=0.0, le=1.0),
    repository: MemoryQdrantRepository = Depends(get_memory_repository),
    embedding_service = Depends(get_embedding_service)
):
    """컬렉션별 검색 + user_id 필터링"""
    try:
        # 쿼리 임베딩 생성
        query_vector = embedding_service.encode(query)
        
        # 검색 실행
        results = repository.search_memory(query_vector, user_id, memory_type, limit)
        
        # 결과 변환
        search_results = []
        for result in results:
            if result.score >= similarity_threshold:
                # 타입별 특화 데이터 추출
                episodic_data = None
                semantic_data = None
                
                if memory_type == MemoryType.EPISODIC:
                    episodic_data = {
                        "speaker": result.metadata.get("speaker"),
                        "emotion": result.metadata.get("emotion"),
                        "context": result.metadata.get("context"),
                        "links": result.metadata.get("links")
                    }
                elif memory_type == MemoryType.SEMANTIC:
                    semantic_data = {
                        "fact_type": result.metadata.get("fact_type"),
                        "confidence_score": result.metadata.get("confidence_score"),
                        "last_updated": result.metadata.get("last_updated")
                    }
                
                search_results.append(MemorySearchResult(
                    id=str(result.id),
                    text=result.metadata.get("text", ""),
                    memory_type=memory_type,
                    collection_name=memory_type.value,
                    score=result.score,
                    user_id=result.metadata.get("user_id"),
                    timestamp=result.metadata.get("timestamp"),
                    importance_score=result.metadata.get("importance_score"),
                    source=result.metadata.get("source"),
                    episodic_data=episodic_data,
                    semantic_data=semantic_data
                ))
        
        return search_results
        
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
    similarity_threshold: float = Query(default=0.0, ge=0.0, le=1.0),
    repository: MemoryQdrantRepository = Depends(get_memory_repository),
    embedding_service = Depends(get_embedding_service)
):
    """다중 컬렉션 통합 검색"""
    try:
        start_time = time.time()
        
        # 가중치 설정
        weights = {
            MemoryType.EPISODIC: episodic_weight,
            MemoryType.SEMANTIC: semantic_weight
        }
        
        # 쿼리 임베딩 생성
        query_vector = embedding_service.encode(query)
        
        # 다중 컬렉션 검색
        results = repository.multi_collection_search(
            query_vector, user_id, collections, limit, weights
        )
        
        # 결과 변환
        search_results = []
        collection_stats = {}
        
        for result in results:
            if result.score >= similarity_threshold:
                memory_type = MemoryType(result.collection_type)
                
                # 통계 업데이트
                collection_stats[result.collection_type] = collection_stats.get(result.collection_type, 0) + 1
                
                # 타입별 특화 데이터 추출
                episodic_data = None
                semantic_data = None
                
                if memory_type == MemoryType.EPISODIC:
                    episodic_data = {
                        "speaker": result.metadata.get("speaker"),
                        "emotion": result.metadata.get("emotion"),
                        "context": result.metadata.get("context"),
                        "links": result.metadata.get("links")
                    }
                elif memory_type == MemoryType.SEMANTIC:
                    semantic_data = {
                        "fact_type": result.metadata.get("fact_type"),
                        "confidence_score": result.metadata.get("confidence_score"),
                        "last_updated": result.metadata.get("last_updated")
                    }
                
                search_results.append(MemorySearchResult(
                    id=str(result.id),
                    text=result.metadata.get("text", ""),
                    memory_type=memory_type,
                    collection_name=result.collection_type,
                    score=result.score,
                    user_id=result.metadata.get("user_id"),
                    timestamp=result.metadata.get("timestamp"),
                    importance_score=result.metadata.get("importance_score"),
                    source=result.metadata.get("source"),
                    episodic_data=episodic_data,
                    semantic_data=semantic_data
                ))
        
        query_time = (time.time() - start_time) * 1000
        
        return MultiCollectionSearchResponse(
            results=search_results,
            collection_stats=collection_stats,
            total_results=len(search_results),
            query_time_ms=query_time,
            user_id=user_id,
            query=query,
            applied_weights={k.value: v for k, v in weights.items()}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"다중 컬렉션 검색 실패: {str(e)}")

@router.post("/classify", response_model=ClassificationResult)
async def classify_text(
    text: str,
    context: Optional[Dict[str, Any]] = None,
    classifier: MemoryClassifier = Depends(get_memory_classifier)
):
    """텍스트 메모리 타입 분류"""
    try:
        classification = classifier.classify_with_confidence(text, context or {})
        explanation = classifier.get_classification_explanation(text, context or {})
        
        return ClassificationResult(
            predicted_type=classification["predicted_type"],
            confidence=classification["confidence"],
            explanation=explanation,
            episodic_score=classification["scores"][MemoryType.EPISODIC],
            semantic_score=classification["scores"][MemoryType.SEMANTIC],
            features=classification["features"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분류 실패: {str(e)}")

@router.get("/user/{user_id}/stats", response_model=UserMemoryStats)
async def get_user_memory_stats(
    user_id: str,
    repository: MemoryQdrantRepository = Depends(get_memory_repository)
):
    """사용자 메모리 통계 조회"""
    try:
        episodic_count = repository.get_user_memory_count(user_id, MemoryType.EPISODIC)
        semantic_count = repository.get_user_memory_count(user_id, MemoryType.SEMANTIC)
        total_memories = episodic_count + semantic_count
        
        # 시간대별 통계 계산
        oldest_memory = None
        newest_memory = None
        daily_average = 0.0
        most_active_day = None
        
        if total_memories > 0:
            # 모든 메모리 타입에서 시간 정보 수집
            all_timestamps = []
            
            for memory_type in [MemoryType.EPISODIC, MemoryType.SEMANTIC]:
                # 샘플 검색으로 시간 정보 수집 (임시 쿼리)
                try:
                    sample_results = repository.search_memory([0.0] * 384, user_id, memory_type, limit=1000)
                    for result in sample_results:
                        timestamp_str = result.metadata.get("timestamp")
                        if timestamp_str:
                            try:
                                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                                all_timestamps.append(timestamp)
                            except:
                                continue
                except:
                    continue
            
            if all_timestamps:
                all_timestamps.sort()
                oldest_memory = all_timestamps[0].isoformat()
                newest_memory = all_timestamps[-1].isoformat()
                
                # 일평균 계산
                time_span = (all_timestamps[-1] - all_timestamps[0]).days
                if time_span > 0:
                    daily_average = total_memories / time_span
                else:
                    daily_average = total_memories  # 같은 날 생성된 경우
                
                # 가장 활발한 날 계산 (간단한 구현)
                date_counts = {}
                for ts in all_timestamps:
                    date_key = ts.date().isoformat()
                    date_counts[date_key] = date_counts.get(date_key, 0) + 1
                
                if date_counts:
                    most_active_day = max(date_counts, key=date_counts.get)
        
        return UserMemoryStats(
            user_id=user_id,
            total_memories=total_memories,
            episodic_count=episodic_count,
            semantic_count=semantic_count,
            oldest_memory=oldest_memory,
            newest_memory=newest_memory,
            daily_average=daily_average,
            most_active_day=most_active_day
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 조회 실패: {str(e)}")

@router.delete("/user/{user_id}/memories")
async def delete_user_memories(
    user_id: str,
    memory_type: Optional[MemoryType] = Query(default=None),
    repository: MemoryQdrantRepository = Depends(get_memory_repository)
):
    """사용자 메모리 삭제"""
    try:
        repository.delete_user_memories(user_id, memory_type)
        
        type_msg = f" ({memory_type.value})" if memory_type else " (전체)"
        return {
            "status": "success",
            "message": f"사용자 {user_id}의 메모리{type_msg}가 삭제되었습니다."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"메모리 삭제 실패: {str(e)}")

@router.post("/collections/{collection_name}/reset")
async def reset_collection(
    collection_name: str,
    repository: MemoryQdrantRepository = Depends(get_memory_repository)
):
    """컬렉션 초기화"""
    try:
        repository.reset_collection(collection_name)
        
        return {
            "status": "success",
            "message": f"컬렉션 {collection_name}이 초기화되었습니다."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"컬렉션 초기화 실패: {str(e)}")

@router.get("/system/stats", response_model=SystemStats)
async def get_system_stats(
    repository: MemoryQdrantRepository = Depends(get_memory_repository)
):
    """시스템 전체 통계"""
    try:
        # 컬렉션별 통계 수집
        collections_info = []
        total_memories = 0
        unique_users = set()
        
        for memory_type in [MemoryType.EPISODIC, MemoryType.SEMANTIC]:
            collection_name = memory_type.value
            
            try:
                # 컬렉션 정보 가져오기
                collection_stats = repository.get_collection_stats(collection_name)
                total_points = collection_stats.points_count
                total_memories += total_points
                
                # 샘플링으로 사용자 수 추정
                sample_results = repository.search_memory([0.0] * 384, "dummy", memory_type, limit=1000)
                users_in_collection = set()
                for result in sample_results:
                    user_id = result.metadata.get("user_id")
                    if user_id:
                        users_in_collection.add(user_id)
                        unique_users.add(user_id)
                
                user_count = len(users_in_collection)
                avg_points_per_user = total_points / max(user_count, 1)
                
                # 컬렉션 설정에서 벡터 차원과 거리 함수 가져오기
                config = repository.collection_configs.get(collection_name, {})
                
                collections_info.append({
                    "name": collection_name,
                    "memory_type": memory_type,
                    "vector_dim": config.get("vector_dim", 384),
                    "distance": config.get("distance", "COSINE"),
                    "total_points": total_points,
                    "user_count": user_count,
                    "avg_points_per_user": avg_points_per_user
                })
                
            except Exception as e:
                # 컬렉션이 없거나 오류 시 기본값
                collections_info.append({
                    "name": collection_name,
                    "memory_type": memory_type,
                    "vector_dim": 384,
                    "distance": "COSINE", 
                    "total_points": 0,
                    "user_count": 0,
                    "avg_points_per_user": 0.0
                })
        
        return SystemStats(
            total_collections=len(collections_info),
            total_users=len(unique_users),
            total_memories=total_memories,
            collections=collections_info,
            avg_query_time_ms=50.0,  # 기본값 (실제 측정 필요)
            classification_accuracy=None,
            uptime_hours=0.0,  # 실제 업타임 계산 필요
            last_updated=datetime.now(timezone.utc).isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시스템 통계 조회 실패: {str(e)}")