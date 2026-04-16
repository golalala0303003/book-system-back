from app.exceptions.base import BusinessException
from fastapi import status
from app.core.constants import ErrorMsg

class BoardAlreadyExistsException(BusinessException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=ErrorMsg.BOARD_ALREADY_EXISTS)

class BoardNotExistsException(BusinessException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=ErrorMsg.BOARD_ALREADY_EXISTS)

class BoardHasBeenBannedException(BusinessException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=ErrorMsg.BOARD_HAS_BEEN_BANNED)

class PostNotExistsException(BusinessException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=ErrorMsg.POST_NOT_EXISTS)

class CommentNotExistsException(BusinessException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=ErrorMsg.COMMENT_NOT_EXISTS)

class InvalidCommentLevelException(BusinessException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=ErrorMsg.INVALID_COMMENT_LEVEL)

class IllegalReportTypeException(BusinessException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail="错误的举报类型")
