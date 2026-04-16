from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

from app.schemas.book_schema import BookVO
from app.schemas.user_schema import UserInfoVO


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
    fav_status: Optional[bool] = None
    creator_id: int
    moderator_id: Optional[int] = None
    create_time: datetime

    model_config = ConfigDict(from_attributes=True)

class BoardAdminQueryDTO(BaseModel):
    page: int = Field(default=1, ge=1, description="当前页码")
    size: int = Field(default=10, ge=1, le=100, description="每页条数")
    keyword: Optional[str] = Field(default=None, description="搜索id/板块名")
    is_active: Optional[bool] = Field(default=None, description="上架状态: True已上架, False已下架, 不传查全部")
    sort_by: str = Field(default="create_time", description="排序字段：id/name/creator_name/post_count")
    sort_order: str = Field(default="desc", description="排序方向：asc (升序), desc (降序)")

class BoardAdminVO(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    cover_url: Optional[str] = None
    creator_id: int
    creator_name: str
    create_time: datetime
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class BoardStatusUpdateDTO(BaseModel):
    """管理员更新板块状态参数"""
    is_active: bool = Field(..., description="目标状态：True为解封/正常，False为封禁/下架")

class BoardSuggestVO(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)

class BoardFavoriteDTO(BaseModel):
    board_id: int = Field(..., description="要收藏的板块ID")
    status: int = Field(..., description="1收藏-1取消收藏")

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
    user: Optional[UserInfoVO] = None
    board_id: int
    book_id: Optional[int] = None
    book: Optional[BookVO] = None
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
    user_name: Optional[str] = None
    user_avatar_url: Optional[str] = None

    parent_id: Optional[int] = None  # 父评论id

    reply_to_user_id: Optional[int] = None
    reply_to_user_name: Optional[str] = None

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

class ReportCreateDTO(BaseModel):
    """用户提交举报的参数"""
    target_type: str = Field(..., description="目标类型：'board', 'post', 或 'comment'")
    target_id: int = Field(..., description="具体的被举报对象ID")
    reason: str = Field(..., max_length=500, description="具体的举报原因")

class ReportAdminQueryDTO(BaseModel):
    """管理员分页查询聚合举报列表参数"""
    page: int = Field(default=1, ge=1)
    size: int = Field(default=10, ge=1, le=100)
    status: int = Field(default=0, description="筛选状态: 0待处理, 1已处理, 2已驳回")
    target_type: Optional[str] = Field(default=None, description="可选过滤: board, post, comment")

class ReportAggregatedVO(BaseModel):
    """管理端展示的聚合举报对象"""
    target_type: str
    target_id: int
    report_count: int = Field(description="该对象被举报的总次数")
    latest_report_time: datetime = Field(description="最近一次被举报的时间")
    target_preview_text: str = Field(default="[目标已删除或无法预览]", description="帖子标题或评论内容预览")

class ReportDetailVO(BaseModel):
    """单一举报记录的详细信息"""
    id: int
    user_id: int
    reason: str
    create_time: datetime
    process_remark: Optional[str] = Field(default=None, description="管理员处理备注")

    model_config = ConfigDict(from_attributes=True)

class ReportProcessDTO(BaseModel):
    """管理员处理举报的请求参数"""
    target_type: str = Field(..., description="目标类型: 'board', 'post', 'comment'")
    target_id: int = Field(..., description="目标ID")
    action: int = Field(..., description="处理结果: 1=判定违规并下架, 2=判定合法并驳回")
    remark: Optional[str] = Field(default=None, description="处理备注")