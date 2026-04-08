from app.exceptions.base import BusinessException
from fastapi import status
from app.core.constants import ErrorMsg

class LLMNotAvailableException(BusinessException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=ErrorMsg.LLM_NOT_AVAILABLE)
