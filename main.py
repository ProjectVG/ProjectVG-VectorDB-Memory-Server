from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
import uuid
import os

# 초기화
app = FastAPI()
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Qdrant 연결 (Docker용 환경변수 사용)
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

# 컬렉션이 존재하는지 확인
COLLECTION_NAME = "my_vectors"
if COLLECTION_NAME not in qdrant.get_collections().collections:
    qdrant.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE)
    )

# 요청 모델
class InsertRequest(BaseModel):
    text: str
    metadata: dict = {}

class SearchRequest(BaseModel):
    query: str
    top_k: int = 3

# 라우트
@app.post("/insert")
def insert(req: InsertRequest):
    vector = model.encode(req.text).tolist()
    point = PointStruct(
        id=str(uuid.uuid4()),
        vector=vector,
        payload={"text": req.text, **req.metadata}
    )
    qdrant.upsert(collection_name=COLLECTION_NAME, points=[point])
    return {"status": "ok"}

@app.post("/search")
def search(req: SearchRequest):
    query_vector = model.encode(req.query).tolist()
    results = qdrant.query_points(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        limit=req.top_k
    )
    return [
        {
            "text": r.payload.get("text"),
            "score": r.score
        }
        for r in results
    ]
