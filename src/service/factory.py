from sentence_transformers import SentenceTransformer
from src.repository import VectorDBRepository
from src.service.memory_service import MemoryService
from src.config import settings

_model = None
_service = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.model_name)
    return _model

def get_memory_service():
    global _service
    if _service is None:
        repo = VectorDBRepository()
        _service = MemoryService(get_model(), repo)
    return _service 