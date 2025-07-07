from fastapi import Request
from fastapi.responses import JSONResponse
from src.utils import AppException, VectorDBConnectionError, ModelEncodeError, InvalidRequestError

async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc) or "서버 내부 오류", "type": exc.__class__.__name__}
    )

async def vectordb_exception_handler(request: Request, exc: VectorDBConnectionError):
    return JSONResponse(
        status_code=502,
        content={"detail": str(exc) or "벡터 DB 연결 오류", "type": "VectorDBConnectionError"}
    )

async def model_encode_exception_handler(request: Request, exc: ModelEncodeError):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc) or "임베딩 모델 인코딩 오류", "type": "ModelEncodeError"}
    )

async def invalid_request_exception_handler(request: Request, exc: InvalidRequestError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc) or "잘못된 요청 데이터", "type": "InvalidRequestError"}
    ) 