from pydantic import BaseModel, Field, field_validator
import re
from typing import List, Dict, Optional
from datetime import datetime

class InsertRequest(BaseModel):
    collection: str = Field(default="default", min_length=1, max_length=255)
    text: str
    metadata: dict = {}
    timestamp: str = None
    user_id: str = Field(default="anonymous", min_length=1, max_length=50)
    
    @field_validator('collection')
    @classmethod
    def validate_collection_name(cls, v):
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_-]*$', v):
            raise ValueError('컬렉션 이름은 영문자, 숫자, 언더스코어(_), 하이픈(-)만 사용 가능하며, 영문자나 언더스코어로 시작해야 합니다.')
        return v
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('사용자 ID는 영문자, 숫자, 언더스코어(_), 하이픈(-)만 사용 가능합니다.')
        return v

class SearchRequest(BaseModel):
    collection: str = Field(default="default", min_length=1, max_length=255)
    query: str
    top_k: int = 3
    time_weight: float = 0.3
    reference_time: str = None
    user_id: str = Field(default="anonymous", min_length=1, max_length=50)
    
    @field_validator('collection')
    @classmethod
    def validate_collection_name(cls, v):
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_-]*$', v):
            raise ValueError('컬렉션 이름은 영문자, 숫자, 언더스코어(_), 하이픈(-)만 사용 가능하며, 영문자나 언더스코어로 시작해야 합니다.')
        return v
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('사용자 ID는 영문자, 숫자, 언더스코어(_), 하이픈(-)만 사용 가능합니다.')
        return v

class AdvancedSearchRequest(BaseModel):
    """고급 검색 요청 모델"""
    user_id: str = Field(default="anonymous", min_length=1, max_length=50)
    query: str
    top_k: int = 5
    search_strategy: str = Field(default="hybrid", description="검색 전략: hybrid, semantic, keyword, temporal")
    
    # 시간 필터링
    time_range: Optional[Dict] = None  # {"start": "2024-01-01", "end": "2024-01-31"}
    time_weight: float = 0.3
    
    # 메모리 타입 필터링
    memory_types: Optional[List[str]] = None  # ["episodic", "semantic", "emotional"]
    
    # 개체명 필터링
    entities: Optional[List[Dict]] = None  # [{"type": "food", "value": "피자"}]
    
    # 컨텍스트 필터링
    context_filters: Optional[Dict] = None  # {"location": "집", "emotion": "기쁨"}
    
    # 검색 옵션
    include_metadata: bool = True
    include_embeddings: bool = False
    similarity_threshold: float = 0.5
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('사용자 ID는 영문자, 숫자, 언더스코어(_), 하이픈(-)만 사용 가능합니다.')
        return v
    
    @field_validator('search_strategy')
    @classmethod
    def validate_search_strategy(cls, v):
        valid_strategies = ["hybrid", "semantic", "keyword", "temporal", "contextual"]
        if v not in valid_strategies:
            raise ValueError(f'검색 전략은 {valid_strategies} 중 하나여야 합니다.')
        return v

class MemoryMetadata(BaseModel):
    """메모리 메타데이터 모델"""
    user_id: str
    memory_type: str
    importance: float = 0.5
    entities: List[Dict] = []
    context: Dict = {}
    tags: List[str] = []
    source: str = "user_input"
    confidence: float = 1.0
    
    # 시간 관련
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # 감정 관련
    emotion: Optional[str] = None
    sentiment_score: Optional[float] = None
    
    # 위치 관련
    location: Optional[str] = None
    coordinates: Optional[Dict] = None
    
    # 관계 관련
    people: List[str] = []
    activities: List[str] = []
    
    # 추가 메타데이터
    custom_fields: Dict = {} 