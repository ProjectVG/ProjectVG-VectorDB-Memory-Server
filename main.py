from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
import uuid
import os
from datetime import datetime, timezone
import math

app = FastAPI()
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

COLLECTION_NAME = "my_vectors"
if COLLECTION_NAME not in qdrant.get_collections().collections:
    qdrant.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE)
    )

class InsertRequest(BaseModel):
    text: str
    metadata: dict = {}
    timestamp: str = None

class SearchRequest(BaseModel):
    query: str
    top_k: int = 3
    time_weight: float = 0.3
    reference_time: str = None

def calculate_time_weight(insert_time: datetime, reference_time: datetime, time_weight: float) -> float:
    if time_weight == 0.0:
        return 1.0
    
    time_diff = abs((reference_time - insert_time).total_seconds() / 86400)
    decay_factor = math.exp(-time_diff * time_weight)
    
    return decay_factor

def get_current_iso_time() -> str:
    return datetime.now(timezone.utc).isoformat()

def parse_iso_time(time_str: str) -> datetime:
    if time_str.endswith('Z'):
        time_str = time_str[:-1] + '+00:00'
    return datetime.fromisoformat(time_str)

@app.post("/insert")
def insert(req: InsertRequest):
    if req.timestamp:
        insert_time = parse_iso_time(req.timestamp)
    else:
        insert_time = datetime.now(timezone.utc)
        req.timestamp = insert_time.isoformat()
    
    vector = model.encode(req.text).tolist()
    
    metadata = {
        "text": req.text,
        "timestamp": req.timestamp,
        "insert_time": insert_time.isoformat(),
        **req.metadata
    }
    
    point = PointStruct(
        id=str(uuid.uuid4()),
        vector=vector,
        payload=metadata
    )
    qdrant.upsert(collection_name=COLLECTION_NAME, points=[point])
    return {"status": "ok", "timestamp": req.timestamp}

@app.post("/search")
def search(req: SearchRequest):
    if req.reference_time:
        reference_time = parse_iso_time(req.reference_time)
    else:
        reference_time = datetime.now(timezone.utc)
    
    query_vector = model.encode(req.query).tolist()
    
    search_limit = min(req.top_k * 3, 50)
    results = qdrant.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        limit=search_limit
    )
    
    weighted_results = []
    for result in results:
        similarity_score = result.score
        
        payload = result.payload
        if "insert_time" in payload:
            insert_time = parse_iso_time(payload["insert_time"])
            time_weight = calculate_time_weight(insert_time, reference_time, req.time_weight)
        else:
            time_weight = 0.5
        
        final_score = similarity_score * time_weight
        
        weighted_results.append({
            "text": payload.get("text"),
            "similarity_score": similarity_score,
            "time_weight": time_weight,
            "final_score": final_score,
            "timestamp": payload.get("timestamp"),
            "metadata": {k: v for k, v in payload.items() if k not in ["text", "timestamp", "insert_time"]}
        })
    
    weighted_results.sort(key=lambda x: x["final_score"], reverse=True)
    
    return weighted_results[:req.top_k]

@app.get("/time")
def get_current_time():
    """현재 서버 시간을 ISO 형식으로 반환"""
    return {"current_time": get_current_iso_time()}

@app.get("/stats")
def get_collection_stats():
    """컬렉션의 통계 정보를 반환"""
    try:
        collection_info = qdrant.get_collection(COLLECTION_NAME)
        return {
            "collection_name": COLLECTION_NAME,
            "vector_count": collection_info.points_count,
            "vector_size": collection_info.config.params.vectors.size,
            "distance": collection_info.config.params.vectors.distance.value
        }
    except Exception as e:
        return {"error": str(e)}
