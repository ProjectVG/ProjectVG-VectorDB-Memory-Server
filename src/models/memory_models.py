from pydantic import BaseModel, Field, field_validator
import re
from typing import List, Dict, Optional, Any
from datetime import datetime
from src.config.settings import MemoryType

class MemoryInsertRequest(BaseModel):
    """메모리 삽입 요청 모델 (다중 컬렉션 지원)"""
    text: str = Field(description="저장할 텍스트 내용")
    user_id: str = Field(min_length=1, max_length=50, description="사용자 ID")
    memory_type: Optional[MemoryType] = Field(default=None, description="메모리 타입 (자동 분류시 None)")
    
    # 공통 메타데이터
    timestamp: Optional[str] = Field(default=None, description="타임스탬프 (ISO 형식)")
    importance_score: float = Field(default=0.5, ge=0.0, le=1.0, description="중요도 점수")
    source: str = Field(default="conversation", description="메모리 생성 출처")
    
    # Episodic Memory 전용 필드
    speaker: Optional[str] = Field(default=None, description="발화자 (user | ai)")
    emotion: Optional[Dict[str, Any]] = Field(default=None, description="감정 정보")
    context: Optional[Dict[str, Any]] = Field(default=None, description="상황 정보")
    links: Optional[List[str]] = Field(default=None, description="연관된 메모리 ID 목록")
    
    # Semantic Memory 전용 필드  
    fact_type: Optional[str] = Field(default=None, description="사실 유형 (personal_fact | world_fact | ai_persona)")
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0, description="신뢰도 점수")
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('사용자 ID는 영문자, 숫자, 언더스코어(_), 하이픈(-)만 사용 가능합니다.')
        return v

class MemorySearchRequest(BaseModel):
    """메모리 검색 요청 모델 (다중 컬렉션 지원)"""
    query: str = Field(description="검색 쿼리")
    user_id: str = Field(min_length=1, max_length=50, description="사용자 ID")
    memory_type: Optional[MemoryType] = Field(default=None, description="검색할 메모리 타입 (None이면 모든 타입)")
    limit: int = Field(default=10, ge=1, le=100, description="반환할 결과 수")
    
    # 검색 필터
    filters: Optional[Dict[str, Any]] = Field(default=None, description="추가 검색 필터")
    similarity_threshold: float = Field(default=0.0, ge=0.0, le=1.0, description="유사도 임계값")
    
    # 시간 기반 검색
    time_range: Optional[Dict[str, str]] = Field(default=None, description="시간 범위 필터")
    time_weight: float = Field(default=0.3, ge=0.0, le=1.0, description="시간 가중치")
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('사용자 ID는 영문자, 숫자, 언더스코어(_), 하이픈(-)만 사용 가능합니다.')
        return v

class MultiCollectionSearchRequest(BaseModel):
    """다중 컬렉션 통합 검색 요청 모델"""
    query: str = Field(description="검색 쿼리")
    user_id: str = Field(min_length=1, max_length=50, description="사용자 ID")
    collections: List[MemoryType] = Field(default=[MemoryType.EPISODIC, MemoryType.SEMANTIC], description="검색할 컬렉션 목록")
    limit: int = Field(default=10, ge=1, le=100, description="반환할 결과 수")
    
    # 가중치 설정
    weights: Optional[Dict[str, float]] = Field(default=None, description="컬렉션별 가중치")
    
    # 검색 옵션
    include_classification: bool = Field(default=False, description="분류 정보 포함 여부")
    similarity_threshold: float = Field(default=0.0, ge=0.0, le=1.0, description="유사도 임계값")
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('사용자 ID는 영문자, 숫자, 언더스코어(_), 하이픈(-)만 사용 가능합니다.')
        return v

class MemoryInsertResponse(BaseModel):
    """메모리 삽입 응답 모델"""
    id: str = Field(description="생성된 메모리 ID")
    memory_type: MemoryType = Field(description="분류된 메모리 타입")
    collection_name: str = Field(description="저장된 컬렉션 이름")
    user_id: str = Field(description="사용자 ID")
    timestamp: str = Field(description="생성 시간")
    
    # 분류 정보
    classification_confidence: Optional[float] = Field(default=None, description="분류 신뢰도")
    classification_explanation: Optional[str] = Field(default=None, description="분류 이유")

class MemorySearchResult(BaseModel):
    """메모리 검색 결과 모델"""
    id: str = Field(description="메모리 ID")
    text: str = Field(description="메모리 텍스트 내용")
    memory_type: MemoryType = Field(description="메모리 타입")
    collection_name: str = Field(description="컬렉션 이름")
    score: float = Field(description="유사도 점수")
    
    # 메타데이터
    user_id: str = Field(description="사용자 ID")
    timestamp: Optional[str] = Field(default=None, description="생성 시간")
    importance_score: Optional[float] = Field(default=None, description="중요도 점수")
    source: Optional[str] = Field(default=None, description="출처")
    
    # 타입별 특화 데이터
    episodic_data: Optional[Dict[str, Any]] = Field(default=None, description="Episodic 메모리 데이터")
    semantic_data: Optional[Dict[str, Any]] = Field(default=None, description="Semantic 메모리 데이터")

class MultiCollectionSearchResponse(BaseModel):
    """다중 컬렉션 검색 응답 모델"""
    results: List[MemorySearchResult] = Field(description="검색 결과 목록")
    collection_stats: Dict[str, int] = Field(description="컬렉션별 결과 수")
    total_results: int = Field(description="전체 결과 수")
    query_time_ms: float = Field(description="쿼리 실행 시간 (밀리초)")
    
    # 검색 메타데이터
    user_id: str = Field(description="사용자 ID")
    query: str = Field(description="검색 쿼리")
    applied_weights: Optional[Dict[str, float]] = Field(default=None, description="적용된 가중치")

class UserMemoryStats(BaseModel):
    """사용자 메모리 통계 모델"""
    user_id: str = Field(description="사용자 ID")
    total_memories: int = Field(description="전체 메모리 수")
    episodic_count: int = Field(description="Episodic 메모리 수")
    semantic_count: int = Field(description="Semantic 메모리 수")
    
    # 시간 통계
    oldest_memory: Optional[str] = Field(default=None, description="가장 오래된 메모리 시간")
    newest_memory: Optional[str] = Field(default=None, description="가장 최근 메모리 시간")
    
    # 활동 통계
    daily_average: float = Field(description="일평균 메모리 생성 수")
    most_active_day: Optional[str] = Field(default=None, description="가장 활발한 날")

class ClassificationResult(BaseModel):
    """메모리 분류 결과 모델"""
    predicted_type: MemoryType = Field(description="예측된 메모리 타입")
    confidence: float = Field(description="분류 신뢰도")
    explanation: str = Field(description="분류 이유 설명")
    
    # 상세 점수
    episodic_score: float = Field(description="Episodic 점수")
    semantic_score: float = Field(description="Semantic 점수")
    
    # 분석 특징
    features: Dict[str, int] = Field(description="분석된 특징 수")

class CollectionInfo(BaseModel):
    """컬렉션 정보 모델"""
    name: str = Field(description="컬렉션 이름")
    memory_type: MemoryType = Field(description="메모리 타입")
    vector_dim: int = Field(description="벡터 차원")
    distance: str = Field(description="거리 함수")
    total_points: int = Field(description="전체 포인트 수")
    
    # 사용자 통계
    user_count: int = Field(description="사용자 수")
    avg_points_per_user: float = Field(description="사용자당 평균 포인트 수")

class SystemStats(BaseModel):
    """시스템 전체 통계 모델"""
    total_collections: int = Field(description="전체 컬렉션 수")
    total_users: int = Field(description="전체 사용자 수")  
    total_memories: int = Field(description="전체 메모리 수")
    
    # 컬렉션별 통계
    collections: List[CollectionInfo] = Field(description="컬렉션 정보 목록")
    
    # 성능 통계
    avg_query_time_ms: float = Field(description="평균 쿼리 시간")
    classification_accuracy: Optional[float] = Field(default=None, description="분류 정확도")
    
    # 시스템 정보
    uptime_hours: float = Field(description="시스템 업타임")
    last_updated: str = Field(description="마지막 업데이트 시간")