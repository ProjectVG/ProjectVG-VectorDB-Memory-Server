import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    qdrant_host: str = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port: int = int(os.getenv("QDRANT_PORT", "6333"))
    collection_name: str = "my_vectors"
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"

settings = Settings() 