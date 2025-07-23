from pydantic import BaseModel

class InsertRequest(BaseModel):
    text: str
    metadata: dict = {}
    timestamp: str = None
    user_id: str = None

class SearchRequest(BaseModel):
    query: str
    top_k: int = 3
    time_weight: float = 0.3
    reference_time: str = None
    user_id: str = None 