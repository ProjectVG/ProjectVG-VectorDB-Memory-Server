from pydantic import BaseModel
from typing import Any, Dict, List, Optional

class InsertResponse(BaseModel):
    status: str
    timestamp: str

class SearchResult(BaseModel):
    text: str
    similarity_score: float
    time_weight: float
    final_score: float
    timestamp: Optional[str] = None
    metadata: Dict[str, Any] = {}

SearchResponse = List[SearchResult] 