from fastapi import FastAPI
from src.api.system_routes import system_router
from src.api.memory_routes import router as memory_router
from src.api.user_routes import router as user_router
from src.api.classification_routes import router as classification_router
from src.api.admin_routes import router as admin_router
from src.api.help_routes import router as help_router
from src.api.exception_handlers import (
    app_exception_handler,
    vectordb_exception_handler,
    model_encode_exception_handler,
    invalid_request_exception_handler
)
from src.utils import AppException, VectorDBConnectionError, ModelEncodeError, InvalidRequestError
from src.utils.logger import setup_logging, get_logger, get_uvicorn_custom_log
from src.config.settings import server_config
import uvicorn

# 로깅 설정
setup_logging()

# FastAPI 앱 생성
app = FastAPI(
    title="Memory Server API V2",
    description="""
    FastAPI와 Qdrant를 사용한 다중 컬렉션 벡터 기반 메모리 서버
    
    **V2 특징**:
    - Facade 패턴을 적용한 깔끔한 아키텍처
    - 역할별로 분리된 API 라우터
    - SOLID 원칙을 준수한 서비스 레이어
    - AI 기반 메모리 분류 시스템
    """,
    version="2.0.0"
)

# 예외 핸들러 등록
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(VectorDBConnectionError, vectordb_exception_handler)
app.add_exception_handler(ModelEncodeError, model_encode_exception_handler)
app.add_exception_handler(InvalidRequestError, invalid_request_exception_handler)

# 라우터 등록 - 역할별로 분리된 구조
app.include_router(system_router)           # 시스템 헬스체크 및 기본 정보
app.include_router(memory_router)           # 메모리 삽입 및 검색
app.include_router(user_router)             # 사용자 관리 및 통계
app.include_router(classification_router)   # 분류 및 분석
app.include_router(admin_router)            # 시스템 관리 (관리자용)
app.include_router(help_router)             # API 도움말 및 문서

logger = get_logger(__name__)

if __name__ == "__main__":
    port = server_config.server_port
    host = server_config.server_host
    
    logger.info(f"서버 시작 중... (Host: {host}, Port: {port})")
    
    uvicorn.run(
        app, 
        host=host, 
        port=port,
        log_config=get_uvicorn_custom_log(),
        access_log=True
    ) 