from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


# ================= 板块 DTO,VO =================
class BoardCreateDTO(BaseModel):
    name: str = Field(..., max_length=50, description="板块名称")
    description: Optional[str] = Field(default=None, max_length=255, description="板块简介")
    cover_url: Optional[str] = Field(default=None, max_length=255, description="封面图片")


class BoardDeleteDTO(BaseModel):
    board_id: int = Field(..., description="要删除的板块ID")


class BoardVO(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    cover_url: Optional[str] = None
    creator_id: int
    moderator_id: Optional[int] = None
    create_time: datetime

    model_config = ConfigDict(from_attributes=True)


# ================= 帖子 DTO & VO =================
class PostCreateDTO(BaseModel):
    board_id: int = Field(..., description="所属板块ID")
    title: str = Field(..., max_length=100, description="帖子标题")
    content: str = Field(..., description="帖子富文本正文")
    cover_image: Optional[str] = Field(default=None, max_length=255, description="单张封面图")
    book_id: Optional[int] = Field(default=None, description="关联的书籍ID（可选）")


class PostDeleteDTO(BaseModel):
    post_id: int = Field(..., description="要删除的帖子ID")


class PostVO(BaseModel):
    id: int
    title: str
    content: str
    cover_image: Optional[str] = None
    user_id: int
    board_id: int
    book_id: Optional[int] = None
    view_count: int
    upvote_count: int
    downvote_count: int
    comment_count: int

    my_vote: int = Field(default=0, description="当前用户状态：1赞，-1踩，0未操作或未登录")

    create_time: datetime
    update_time: datetime

    model_config = ConfigDict(from_attributes=True)


class PostQueryDTO(BaseModel):
    page: int = Field(default=1, ge=1, description="当前页码")
    size: int = Field(default=10, ge=1, le=100, description="每页条数")
    board_id: Optional[int] = Field(default=None, description="按板块筛选")
    book_id: Optional[int] = Field(default=None, description="按书籍筛选")
    keyword: Optional[str] = Field(default=None, description="按标题模糊搜索")
    user_id: Optional[int] = Field(default=None, description="按发帖人筛选(用于个人主页历史记录)")

    # 排序控制字段
    sort_by: str = Field(
        default="time",
        description="排序维度: time(按时间最新), upvote(按点赞最多), view(按浏览量最多)"
    )


class PostUpdateDTO(BaseModel):
    post_id: int = Field(..., description="要修改的帖子ID")
    # 以下字段全为 Optional，前端传了哪个就改哪个
    title: Optional[str] = Field(default=None, max_length=100, description="新标题")
    content: Optional[str] = Field(default=None, description="新正文")
    cover_image: Optional[str] = Field(default=None, max_length=255, description="新封面")


# ================= 评论 DTO & VO =================
class CommentCreateDTO(BaseModel):
    post_id: int = Field(..., description="所属帖子ID")
    content: str = Field(..., description="评论内容")
    parent_id: Optional[int] = Field(default=None, description="根评论ID (为空代表直接回复帖子)")
    reply_to_user_id: Optional[int] = Field(default=None, description="被回复的用户ID (二级评论 @ 用户时传)")


class CommentDeleteDTO(BaseModel):
    comment_id: int = Field(..., description="要删除的评论ID")


# 基础评论结构
class CommentVO(BaseModel):
    id: int
    post_id: int
    user_id: int
    parent_id: Optional[int] = None
    reply_to_user_id: Optional[int] = None
    content: str
    upvote_count: int
    downvote_count: int

    my_vote: int = Field(default=0, description="当前用户状态：1赞，-1踩，0未操作或未登录")

    create_time: datetime

    model_config = ConfigDict(from_attributes=True)


# 一级评论
class RootCommentVO(CommentVO):
    children: List[CommentVO] = Field(default_factory=list, description="二级评论列表")


# ================= 互动/点赞 DTO =================
class PostVoteDTO(BaseModel):
    post_id: int = Field(..., description="目标帖子ID")
    vote_type: int = Field(..., description="操作类型：1 为赞，-1 为踩")

class CommentVoteDTO(BaseModel):
    comment_id: int = Field(..., description="目标评论ID")
    vote_type: int = Field(..., description="操作类型：1 为赞，-1 为踩")