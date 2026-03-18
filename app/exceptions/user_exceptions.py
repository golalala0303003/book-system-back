from fastapi import status
from app.exceptions.base import BusinessException
from app.core.constants import ErrorMsg

class UserAlreadyExistsException(BusinessException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=ErrorMsg.USER_ALREADY_EXISTS)

class InvalidCredentialsException(BusinessException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorMsg.INVALID_CREDENTIALS,
            headers={"WWW-Authenticate": "Bearer"}
        )

class AuthFailedException(BusinessException):
    def __init__(self, detail: str = ErrorMsg.TOKEN_EXPIRED):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )