from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime, Text, func, UniqueConstraint


# 板块表
class Board(SQLModel, table=True):
    __tablename__ = "board"

    id: Optional[int] = Field(default=None, primary_key=True)  # 主键id
    name: str = Field(index=True, unique=True, max_length=50)  # 板块名称，如"科幻"
    description: Optional[str] = Field(default=None, max_length=255)  # 简介
    cover_url: Optional[str] = Field(default=None, max_length=255)  # 板块封面图
    creator_id: int = Field(index=True)  # 创建者ID
    moderator_id: Optional[int] = Field(default=None, index=True)  # 版主ID 暂时无用
    is_active: bool = Field(default=True)  # 状态：True正常，False隐藏封禁

    create_time: datetime = Field(sa_column=Column(DateTime, server_default=func.now(), nullable=False))
    update_time: datetime = Field(
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    )


# 帖子表
class Post(SQLModel, table=True):
    __tablename__ = "post"

    id: Optional[int] = Field(default=None, primary_key=True)  # 主键id
    title: str = Field(index=True, max_length=100)  # 标题
    content: str = Field(sa_column=Column(Text, nullable=False))  # 文章富文本
    cover_image: Optional[str] = Field(default=None, max_length=255)  # 可选的文章单张封面图
    user_id: int = Field(index=True)  # 发帖人ID
    board_id: int = Field(index=True)  # 所属板块ID
    book_id: Optional[int] = Field(default=None, index=True)  # 关联书籍ID (逻辑外键)

    view_count: int = Field(default=0)  # 浏览量
    upvote_count: int = Field(default=0)  # 点赞数
    downvote_count: int = Field(default=0)  # 踩数
    comment_count: int = Field(default=0)  # 评论总数 (冗余字段，提升查询性能)

    is_deleted: bool = Field(default=False)  # 逻辑删除标志

    create_time: datetime = Field(sa_column=Column(DateTime, server_default=func.now(), nullable=False))
    update_time: datetime = Field(
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    )


# 评论表
class Comment(SQLModel, table=True):
    __tablename__ = "comment"

    id: Optional[int] = Field(default=None, primary_key=True)  # 主键id
    post_id: int = Field(index=True)  # 所属帖子ID
    user_id: int = Field(index=True)  # 评论人ID

    parent_id: Optional[int] = Field(default=None, index=True)  # 根评论ID (为空则为一级评论)
    reply_to_user_id: Optional[int] = Field(default=None)  # 被回复人ID (用于二级评论 @ 用户, 为空为一级评论)

    content: str = Field(sa_column=Column(Text, nullable=False))  # 评论内容

    upvote_count: int = Field(default=0)  # 点赞数
    downvote_count: int = Field(default=0)  # 踩数

    is_deleted: bool = Field(default=False)  # 逻辑删除

    create_time: datetime = Field(sa_column=Column(DateTime, server_default=func.now(), nullable=False))


# 帖子赞踩记录表 (PostVote)
class PostVote(SQLModel, table=True):
    __tablename__ = "post_vote"

    # 联合唯一索引：确保一个用户对一个帖子只能有一条评价记录
    __table_args__ = (UniqueConstraint("user_id", "post_id", name="uq_user_post_vote"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    post_id: int = Field(index=True)
    vote_type: int = Field(...)  # 1 为赞，-1 为踩

    create_time: datetime = Field(sa_column=Column(DateTime, server_default=func.now(), nullable=False))


# 5. 评论赞踩记录表 (CommentVote)
class CommentVote(SQLModel, table=True):
    __tablename__ = "comment_vote"

    # 联合唯一索引：确保一个用户对一条评论只能有一条评价记录
    __table_args__ = (UniqueConstraint("user_id", "comment_id", name="uq_user_comment_vote"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    comment_id: int = Field(index=True)
    vote_type: int = Field(...)  # 1 为赞，-1 为踩

    create_time: datetime = Field(sa_column=Column(DateTime, server_default=func.now(), nullable=False))