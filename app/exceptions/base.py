from fastapi import HTTPException

class BusinessException(HTTPException):
    """所有业务异常的顶级基类"""
    def __init__(self, status_code: int, detail: str, headers: dict | None = None):
        super().__init__(status_code=status_code, detail=detail, headers=headers)