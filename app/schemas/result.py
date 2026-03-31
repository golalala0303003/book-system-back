from typing import Generic, TypeVar, Optional, Any, List
from pydantic import BaseModel

T = TypeVar("T")

class Result(BaseModel, Generic[T]):
    code: int = 200
    message: str = "success"
    data: Optional[T] = None

    @staticmethod
    def success(data: Any = None, message: str = "success"):
        return Result(code=200, message=message, data=data)

    @staticmethod
    def fail(code: int = 400, message: str = "error", data: Any = None):
        return Result(code=code, message=message, data=data)

class PageData(BaseModel, Generic[T]):
    total: int          # 总条数
    page: int           # 当前页码
    size: int           # 每页数量
    records: List[T]    # 当前页的数据列表