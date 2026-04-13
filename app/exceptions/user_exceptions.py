from fastapi import status
from app.exceptions.base import BusinessException
from app.core.constants import ErrorMsg

# 用户已存在
class UserAlreadyExistsException(BusinessException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=ErrorMsg.USER_ALREADY_EXISTS)

# 用户名或密码错误
class InvalidCredentialsException(BusinessException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorMsg.INVALID_CREDENTIALS,
            headers={"WWW-Authenticate": "Bearer"}
        )

# token认证失败
class AuthFailedException(BusinessException):
    def __init__(self, detail: str = ErrorMsg.TOKEN_EXPIRED):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )

class UserNotFoundException(BusinessException):
    """用户不存在的异常"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorMsg.USER_NOT_FOUND
        )

class IncorrectPasswordException(BusinessException):
    """密码错误的异常"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorMsg.INCORRECT_PASSWORD
        )

class AtLeastOneFieldException(BusinessException):
    """修改用户信息一个信息不传的异常"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorMsg.LEAST_ONE_FIELD
        )

class UserNotPermittedException(BusinessException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=ErrorMsg.USER_ALREADY_EXISTS)

class UserNotAllowedException(BusinessException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=ErrorMsg.USER_NOT_ALLOWED)
