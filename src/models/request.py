from pydantic import BaseModel, Field, field_validator
import re

class InsertRequest(BaseModel):
    collection: str = Field(default="default", min_length=1, max_length=255)
    text: str
    metadata: dict = {}
    timestamp: str = None

    @field_validator('collection')
    @classmethod
    def validate_collection_name(cls, v):
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_-]*$', v):
            raise ValueError('컬렉션 이름은 영문자, 숫자, 언더스코어(_), 하이픈(-)만 사용 가능하며, 영문자나 언더스코어로 시작해야 합니다.')
        return v

class SearchRequest(BaseModel):
    collection: str = Field(default="default", min_length=1, max_length=255)
    query: str
    top_k: int = 3
    time_weight: float = 0.3
    reference_time: str = None

    @field_validator('collection')
    @classmethod
    def validate_collection_name(cls, v):
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_-]*$', v):
            raise ValueError('컬렉션 이름은 영문자, 숫자, 언더스코어(_), 하이픈(-)만 사용 가능하며, 영문자나 언더스코어로 시작해야 합니다.')
        return v 