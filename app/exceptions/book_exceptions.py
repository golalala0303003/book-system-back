from app.exceptions.base import BusinessException
from fastapi import status
from app.core.constants import ErrorMsg

class BookNotExistsException(BusinessException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=ErrorMsg.BOOK_NOT_EXISTS)


class BookAlreadyExistsException(BusinessException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=ErrorMsg.BOOK_ALREADY_EXISTS)
