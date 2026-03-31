from fastapi import APIRouter, Depends

from app.core.constants import SuccessMsg
from app.models.user import User
from app.dependencies import get_current_user, get_current_user_optional
from app.service.forum_service import ForumService
from app.schemas.forum_schema import BoardCreateDTO, BoardDeleteDTO, BoardVO, PostQueryDTO, PostUpdateDTO, \
    CommentCreateDTO, CommentDeleteDTO, PostVoteDTO, CommentVoteDTO
from app.schemas.forum_schema import PostCreateDTO, PostDeleteDTO, PostVO
from app.schemas.result import Result
from typing import Optional

board_router = APIRouter(prefix="/board", tags=["论坛-板块模块"])
post_router = APIRouter(prefix="/post", tags=["论坛-帖子模块"])
comment_router = APIRouter(prefix="/comment", tags=["论坛-评论模块"])

@board_router.post("/create")
def create_board(
    dto: BoardCreateDTO,
    current_user: User = Depends(get_current_user),
    service: ForumService = Depends()
):
    """创建新板块 (需要登录鉴权，所有登录用户可创建)"""
    board_vo = service.create_board(dto, current_user)
    return Result.success(data=board_vo, message=SuccessMsg.BOARD_CREATE_SUCCESS)


@board_router.post("/delete")
def delete_board(
    dto: BoardDeleteDTO,
    current_user: User = Depends(get_current_user),
    service: ForumService = Depends()
):
    """删除/隐藏板块 (需要登录鉴权,仅限管理员)"""
    service.delete_board(dto.board_id, current_user)
    return Result.success(message=SuccessMsg.BOARD_DELETE_SUCCESS)

@board_router.get("/list")
def get_board_list(
    service: ForumService = Depends()
):
    """获取所有可用板块列表 (无需登录即可查看)"""
    board_list = service.get_all_boards()
    return Result.success(data=board_list, message=SuccessMsg.GET_BOARD_LIST_SUCCESS)

@post_router.post("/create")
def create_post(
    dto: PostCreateDTO,
    current_user: User = Depends(get_current_user),
    service: ForumService = Depends()
):
    """发布新帖子(需要登录鉴权)"""
    post_vo = service.create_post(dto, current_user)
    return Result.success(data=post_vo, message=SuccessMsg.POST_CREATE_SUCCESS)


@post_router.post("/delete")
def delete_post(
    dto: PostDeleteDTO,
    current_user: User = Depends(get_current_user),
    service: ForumService = Depends()
):
    """删除帖子 (仅限作者或管理员)"""
    service.delete_post(dto.post_id, current_user)
    return Result.success(message=SuccessMsg.POST_DELETE_SUCCESS)


@post_router.get("/detail/{post_id}")
def get_post_detail(
        post_id: int,
        # 可选鉴权：如果没有 token，current_user 就是 None
        current_user: Optional[User] = Depends(get_current_user_optional),
        service: ForumService = Depends()
):
    """查看帖子详情 (游客可用，附带浏览量+1)"""
    post_vo = service.get_post_detail(post_id, current_user)

    # 记录浏览记录
    if current_user:
        service.record_user_view_history(current_user.id, post_id)

    return Result.success(data=post_vo, message=SuccessMsg.POST_DETAIL_SUCCESS)


@post_router.post("/page")
def get_post_page(
        dto: PostQueryDTO,
        current_user: Optional[User] = Depends(get_current_user_optional),
        service: ForumService = Depends()
):
    """通用分页查询帖子 (游客也可以)"""
    page_data = service.get_post_page(dto, current_user)
    return Result.success(data=page_data, message=SuccessMsg.POST_PAGE_SUCCESS)

@post_router.post("/update")
def update_post(
    dto: PostUpdateDTO,
    current_user: User = Depends(get_current_user),
    service: ForumService = Depends()
):
    """修改帖子 (仅限作者本人)"""
    post_vo = service.update_post(dto, current_user)
    return Result.success(data=post_vo, message=SuccessMsg.POST_UPDATE_SUCCESS)

@post_router.post("/vote")
def vote_post(
    dto: PostVoteDTO,
    current_user: User = Depends(get_current_user),
    service: ForumService = Depends()
):
    """帖子点赞/踩 (支持取消与反转)"""
    service.vote_post(dto, current_user)
    return Result.success(message=SuccessMsg.ACTION_SUCCESS)

@comment_router.post("/create")
def create_comment(
    dto: CommentCreateDTO,
    current_user: User = Depends(get_current_user),
    service: ForumService = Depends()
):
    """发表评论/回复"""
    comment_vo = service.create_comment(dto, current_user)
    return Result.success(data=comment_vo, message=SuccessMsg.COMMENT_CREATE_SUCCESS)


@comment_router.post("/delete")
def delete_comment(
    dto: CommentDeleteDTO,
    current_user: User = Depends(get_current_user),
    service: ForumService = Depends()
):
    """删除评论"""
    service.delete_comment(dto.comment_id, current_user)
    return Result.success(message=SuccessMsg.COMMENT_DELETE_SUCCESS)


@comment_router.get("/list/{post_id}")
def get_comment_list(
    post_id: int,
    current_user: User = Depends(get_current_user_optional),
    service: ForumService = Depends()
):
    """获取某帖子下的所有评论 (两级楼中楼结构)"""
    tree_data = service.get_post_comment_tree(post_id, current_user)
    return Result.success(data=tree_data, message=SuccessMsg.GET_COMMENT_LIST_SUCCESS)

@comment_router.post("/vote")
def vote_comment(
    dto: CommentVoteDTO,
    current_user: User = Depends(get_current_user),
    service: ForumService = Depends()
):
    """评论点赞/踩 (支持取消与反转)"""
    service.vote_comment(dto, current_user)
    return Result.success(message=SuccessMsg.ACTION_SUCCESS)

