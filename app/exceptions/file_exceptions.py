from fastapi import status
from app.exceptions.base import BusinessException
from app.core.constants import ErrorMsg

class FileUploadException(BusinessException):
    def __init__(self, detail: str = ErrorMsg.UPLOAD_FAILED):
        # OSS 报错属于服务端内部错误，所以用 500
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)

class InvalidFileTypeException(BusinessException):
    def __init__(self):
        # 客户端传错了格式，用 400
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=ErrorMsg.INVALID_FILE_TYPE)

class FileTooLargeException(BusinessException):
    def __init__(self):
        # 客户端传的文件太大，用 413 Payload Too Large
        super().__init__(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=ErrorMsg.FILE_TOO_LARGE)