from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from src.api import router
from src.utils import AppException, VectorDBConnectionError, ModelEncodeError, InvalidRequestError

app = FastAPI()
app.include_router(router)

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc) or "서버 내부 오류", "type": exc.__class__.__name__}
    )

@app.exception_handler(VectorDBConnectionError)
async def vectordb_exception_handler(request: Request, exc: VectorDBConnectionError):
    return JSONResponse(
        status_code=502,
        content={"detail": str(exc) or "벡터 DB 연결 오류", "type": "VectorDBConnectionError"}
    )

@app.exception_handler(ModelEncodeError)
async def model_encode_exception_handler(request: Request, exc: ModelEncodeError):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc) or "임베딩 모델 인코딩 오류", "type": "ModelEncodeError"}
    )

@app.exception_handler(InvalidRequestError)
async def invalid_request_exception_handler(request: Request, exc: InvalidRequestError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc) or "잘못된 요청 데이터", "type": "InvalidRequestError"}
    ) 