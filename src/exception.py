class AppException(Exception):
    """기본 커스텀 예외 베이스 클래스."""
    pass

class VectorDBConnectionError(AppException):
    """Qdrant 벡터 DB 연결 또는 쿼리 실패 예외."""
    pass

class ModelEncodeError(AppException):
    """문장 임베딩 모델 인코딩 실패 예외."""
    pass

class InvalidRequestError(AppException):
    """잘못된 요청 데이터 예외."""
    pass 