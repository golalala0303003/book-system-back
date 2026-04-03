from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


# 图书查询DTO
class BookQueryDTO(BaseModel):
    page: int = Field(default=1, ge=1, description="当前页码")
    size: int = Field(default=10, ge=1, le=100, description="每页条数")
    keyword: Optional[str] = Field(default=None, description="搜索书名/作者/ISBN")
    tag: Optional[str] = Field(default=None, description="按单一标签筛选")
    sort_by: str = Field(
        default="time",
        description="排序维度: time(最新), hot(浏览量最高), rating(评分最高)"
    )

class BookSuggestVO(BaseModel):
    id: int
    author: Optional[str] = None
    title: str
    isbn: Optional[str] = None
    cover_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

# 图书返回VO
class BookVO(BaseModel):
    id: int
    douban_id: str
    isbn: Optional[str] = None
    title: str
    author: Optional[str] = None
    publisher: Optional[str] = None
    publish_year: Optional[str] = None
    cover_url: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[str] = None
    douban_rating: float

    view_count: int
    favorite_count: int
    upvote_count: int
    downvote_count: int
    post_count: int
    is_active: bool

    # 夹带当前用户的交互状态
    my_vote: int = Field(default=0, description="1赞，-1踩，0未操作")
    my_favorite_status: int = Field(default=0, description="1想读，2在读，3读过，0未收藏")

    model_config = ConfigDict(from_attributes=True)


class BookVoteDTO(BaseModel):
    book_id: int = Field(..., description="目标书籍ID")
    vote_type: int = Field(..., description="操作类型：1 为赞，-1 为踩")

class BookFavoriteDTO(BaseModel):
    book_id: int = Field(..., description="目标书籍ID")
    status: int = Field(..., description="状态：1想读，2在读，3读过 0没收藏,取消收藏")

class BookCreateDTO(BaseModel):
    douban_id: str = Field(..., max_length=50)
    title: str = Field(..., max_length=255)
    isbn: Optional[str] = None
    author: Optional[str] = None
    publisher: Optional[str] = None
    publish_year: Optional[str] = None
    cover_url: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[str] = None
    douban_rating: float = 0.0

class BookUpdateDTO(BaseModel):
    book_id: int = Field(..., description="要修改的书籍ID")
    douban_id: Optional[str] = None
    title: Optional[str] = None
    isbn: Optional[str] = None
    author: Optional[str] = None
    publisher: Optional[str] = None
    publish_year: Optional[str] = None
    cover_url: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[str] = None
    douban_rating: Optional[float] = None

class BookDeleteDTO(BaseModel):
    book_id: int = Field(..., description="要下架的书籍ID")