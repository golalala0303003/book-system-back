from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime, Text, func, UniqueConstraint, String


class Book(SQLModel, table=True):
    __tablename__ = "book"

    # --- 基础标识 ---
    id: Optional[int] = Field(default=None, primary_key=True)
    douban_id: str = Field(index=True, unique=True, max_length=50)  # 外部唯一标识 豆瓣id
    isbn: Optional[str] = Field(default=None, index=True, max_length=50)
    title: str = Field(index=True, max_length=255)  # 标题
    author: Optional[str] = Field(default=None, index=True, max_length=255)  # 作者
    publisher: Optional[str] = Field(default=None, max_length=255)  # 出版社
    publish_year: Optional[str] = Field(default=None, max_length=50)  # 出版年
    cover_url: Optional[str] = Field(default=None, max_length=500)  # OSS封面链接
    summary: Optional[str] = Field(default=None, sa_column=Column(Text))  # 简介内容
    tags: Optional[str] = Field(default=None, max_length=1000)  # 标签(逗号分隔)
    douban_rating: float = Field(default=0.0)  # 外部评分


    view_count: int = Field(default=0)  # 浏览量 (展示热度)
    favorite_count: int = Field(default=0)  # 收藏量/想读数
    upvote_count: int = Field(default=0)  # 点赞数
    downvote_count: int = Field(default=0)  # 踩数
    post_count: int = Field(default=0)  # 关联讨论帖数

    # tf-idf 向量 index:weight,index:weight
    tfidf_vector: Optional[str] = Field(default=None, sa_column=Column(Text))

    # --- 管理状态 ---
    is_active: bool = Field(default=True)  # 是否上架

    create_time: datetime = Field(sa_column=Column(DateTime, server_default=func.now(), nullable=False))
    update_time: datetime = Field(
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    )


class BookVote(SQLModel, table=True):
    __tablename__ = "book_vote"
    __table_args__ = (UniqueConstraint("user_id", "book_id", name="uq_user_book_vote"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    book_id: int = Field(index=True)
    vote_type: int = Field(...) # 1赞, -1踩
    create_time: datetime = Field(sa_column=Column(DateTime, server_default=func.now()))


class BookFavorite(SQLModel, table=True):
    __tablename__ = "book_favorite"
    __table_args__ = (UniqueConstraint("user_id", "book_id", name="uq_user_book_favorite"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    book_id: int = Field(index=True)

    # 状态枚举：1想读, 2在读, 3读过
    status: int = Field(default=1, index=True)

    create_time: datetime = Field(sa_column=Column(DateTime, server_default=func.now()))


class BookBrowseHistory(SQLModel, table=True):
    __tablename__ = "book_browse_history"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    book_id: int = Field(index=True)

    # 记录最后一次浏览时间
    last_view_time: datetime = Field(sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now()))
    # 记录浏览次数，次数越多权重越高
    view_times: int = Field(default=1)

class TagIndex(SQLModel, table=True):
    __tablename__ = "tag_index"

    id: Optional[int] = Field(default=None, primary_key=True)
    tag_name: str = Field(sa_column=Column(String(100, collation="utf8mb4_bin"), unique=True, index=True))
    index_value: int = Field(unique=True) # 对应在向量中的位置 (0, 1, 2...)