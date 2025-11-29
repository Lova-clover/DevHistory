"""Custom exception classes for DevHistory."""
from fastapi import HTTPException, status


class DevHistoryException(Exception):
    """Base exception for DevHistory."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(DevHistoryException):
    """Authentication failed."""
    def __init__(self, message: str = "인증에 실패했습니다"):
        super().__init__(message, status_code=401)


class AuthorizationError(DevHistoryException):
    """Authorization failed."""
    def __init__(self, message: str = "권한이 없습니다"):
        super().__init__(message, status_code=403)


class RateLimitError(DevHistoryException):
    """API rate limit exceeded."""
    def __init__(self, message: str = "API 호출 한도를 초과했습니다"):
        super().__init__(message, status_code=429)


class ExternalAPIError(DevHistoryException):
    """External API call failed."""
    def __init__(self, service: str, message: str = None):
        msg = message or f"{service} API 호출에 실패했습니다"
        super().__init__(msg, status_code=502)


class DataValidationError(DevHistoryException):
    """Data validation failed."""
    def __init__(self, message: str = "데이터 검증에 실패했습니다"):
        super().__init__(message, status_code=400)


class ResourceNotFoundError(DevHistoryException):
    """Resource not found."""
    def __init__(self, resource: str, identifier: str):
        message = f"{resource}을(를) 찾을 수 없습니다: {identifier}"
        super().__init__(message, status_code=404)


class NetworkError(DevHistoryException):
    """Network operation failed."""
    def __init__(self, message: str = "네트워크 오류가 발생했습니다"):
        super().__init__(message, status_code=503)


def handle_http_exception(exc: HTTPException):
    """Convert HTTPException to user-friendly message."""
    status_messages = {
        401: "로그인이 필요합니다",
        403: "접근 권한이 없습니다",
        404: "요청한 리소스를 찾을 수 없습니다",
        429: "너무 많은 요청을 보냈습니다. 잠시 후 다시 시도해주세요",
        500: "서버 오류가 발생했습니다",
        502: "외부 서비스 연결에 실패했습니다",
        503: "서비스를 일시적으로 사용할 수 없습니다",
    }
    
    return {
        "error": status_messages.get(exc.status_code, "오류가 발생했습니다"),
        "detail": str(exc.detail),
        "status_code": exc.status_code
    }
