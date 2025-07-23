from pydantic import BaseModel, Field

class InsertRequest(BaseModel):
    text: str
    metadata: dict = {}
    timestamp: str = None
    collection: str = Field(..., min_length=1, max_length=30)

class SearchRequest(BaseModel):
    query: str
    top_k: int = 3
    time_weight: float = 0.3
    reference_time: str = None
    collection: str = Field(..., min_length=1, max_length=30) 