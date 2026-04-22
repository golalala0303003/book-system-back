from typing import List

from fastapi import APIRouter, Depends, Query

from app.core.constants import SuccessMsg
from app.dependencies import get_current_user, get_current_user_optional, get_current_admin
from app.models import User
from app.schemas.admin_schema import DashboardVO
from app.schemas.book_schema import BookAdminQueryDTO, BookAdminVO, BookStatusUpdateDTO, BookCreateDTO, BookUpdateDTO
from app.schemas.forum_schema import ReportAggregatedVO, ReportAdminQueryDTO, ReportDetailVO, ReportProcessDTO, \
    BoardAdminVO, BoardAdminQueryDTO, BoardStatusUpdateDTO, PostAdminQueryDTO, PostAdminSummaryVO, PostAdminDetailVO, \
    PostStatusUpdateDTO, CommentAdminVO, CommentAdminQueryDTO, CommentStatusUpdateDTO
from app.schemas.result import Result, PageData
from app.schemas.user_schema import UserAdminVO, UserAdminQueryDTO, UserStatusUpdateDTO
from app.service.admin_service import AdminService
from app.service.book_service import BookService
from app.service.forum_service import ForumService
from app.service.user_service import UserService


admin_router = APIRouter(prefix="/admin", tags=["后台管理模块"])


@admin_router.post("/user/page", response_model=Result[PageData[UserAdminVO]])
def get_user_page_for_admin(
    query_dto: UserAdminQueryDTO,
    admin_user: User = Depends(get_current_admin),
    user_service: UserService = Depends()
):
    """
    [管理端] 分页获取用户列表 (支持按用户名、状态筛选)
    """
    page_data = user_service.get_user_page_for_admin(query_dto)
    return Result.success(data=page_data, message="获取用户列表成功")


@admin_router.post("/user/{user_id}/status", response_model=Result)
def update_user_status(
        user_id: int,
        status_dto: UserStatusUpdateDTO,
        admin_user: User = Depends(get_current_admin),
        user_service: UserService = Depends()
):
    """
    [管理端] 调整用户账号状态 (封禁/解封)
    """
    user_service.update_user_status(user_id, status_dto)

    action_msg = "解封" if status_dto.is_active else "封禁"
    return Result.success(message=f"用户{action_msg}操作成功")

@admin_router.post("/book/page", response_model=Result[PageData[BookAdminVO]])
def get_book_page_for_admin(
    query_dto: BookAdminQueryDTO,
    admin_user: User = Depends(get_current_admin),
    book_service: BookService = Depends()
):
    """
    [管理端] 分页获取图书列表 (支持按书名、状态筛选)
    """
    page_data = book_service.get_admin_book_page(query_dto)
    return Result.success(data=page_data, message="获取图书列表成功")

@admin_router.post("/forum/board/page", response_model=Result[PageData[BoardAdminVO]])
def get_board_page(
    dto: BoardAdminQueryDTO,
    current_user: User = Depends(get_current_admin),
    forum_service: ForumService = Depends()
):
    page_data = forum_service.get_board_page_for_admin(dto)
    return Result.success(data=page_data, message=SuccessMsg.GET_BOARD_LIST_SUCCESS)

@admin_router.post("/board/{board_id}/status", response_model=Result)
def update_board_status(
        board_id: int,
        status_dto: BoardStatusUpdateDTO,
        admin_user: User = Depends(get_current_admin), # 严格校验管理员权限
        forum_service: ForumService = Depends()
):
    """
    [管理端] 调整板块状态 (封禁/解封)
    """
    forum_service.update_board_status(board_id, status_dto)

    action_msg = "解封" if status_dto.is_active else "封禁"
    return Result.success(message=f"板块{action_msg}操作成功")

@admin_router.get("/detail/{book_id}")
def get_book_detail(
    book_id: int,
    admin_user: User = Depends(get_current_admin),
    service: BookService = Depends()
):
    """
    [管理端] 获取图书的详细信息，书籍被下架后仍然可以查看
    """
    book_vo = service.get_book_detail_for_admin(book_id)
    return Result.success(data=book_vo, message=SuccessMsg.GET_BOOK_DETAIL_SUCCESS)

@admin_router.post("/book/{book_id}/status", response_model=Result)
def update_book_status(
        book_id: int,
        status_dto: BookStatusUpdateDTO,
        admin_user: User = Depends(get_current_admin),
        book_service: BookService = Depends()
):
    """
    [管理端] 调整图书上架/下架状态
    """
    book_service.update_book_status_for_admin(book_id, status_dto)

    action_msg = "上架" if status_dto.is_active else "下架"
    return Result.success(message=f"图书{action_msg}操作成功")

@admin_router.post("/book/create")
def create_book(
    dto: BookCreateDTO,
    current_user: User = Depends(get_current_admin),
    book_service: BookService = Depends()
):
    """人工录入新书 (仅限管理员)"""
    book_vo = book_service.create_book(dto, current_user)
    return Result.success(data=book_vo, message="书籍录入成功")

@admin_router.post("/book/update")
def update_book(
    dto: BookUpdateDTO,
    current_user: User = Depends(get_current_admin),
    book_service: BookService = Depends()
):
    """修改书籍信息 (仅限管理员，支持部分字段更新)"""
    book_vo = book_service.update_book(dto, current_user)
    return Result.success(data=book_vo, message="书籍修改成功")

@admin_router.post("/post/page", response_model=Result[PageData[PostAdminSummaryVO]])
def get_post_page_for_admin(
    dto: PostAdminQueryDTO,
    admin_user: User = Depends(get_current_admin),
    service: ForumService = Depends()
):
    """[管理端] 分页获取帖子列表"""
    page_data = service.get_post_page_for_admin(dto)
    return Result.success(data=page_data, message="获取帖子列表成功")

@admin_router.get("/post/{post_id}", response_model=Result[PostAdminDetailVO])
def get_post_detail_for_admin(
    post_id: int,
    admin_user: User = Depends(get_current_admin),
    service: ForumService = Depends()
):
    """[管理端] 获取帖子详细信息"""
    detail_vo = service.get_post_detail_for_admin(post_id)
    return Result.success(data=detail_vo, message="获取帖子详情成功")

@admin_router.post("/post/{post_id}/status", response_model=Result)
def update_post_status_for_admin(
    post_id: int,
    status_dto: PostStatusUpdateDTO,
    admin_user: User = Depends(get_current_admin),
    service: ForumService = Depends()
):
    """[管理端] 调整帖子状态 (封禁/恢复)"""
    service.update_post_status(post_id, status_dto)

    actions = []
    if status_dto.is_banned is not None:
        actions.append("封禁" if status_dto.is_banned else "解除封禁")
    if status_dto.is_deleted is not None:
        actions.append("标记为用户删除" if status_dto.is_deleted else "恢复用户误删")

    action_msg = "、".join(actions) if actions else "无状态修改"
    return Result.success(message=f"帖子{action_msg}操作成功")

@admin_router.post("/report/page", response_model=Result[PageData[ReportAggregatedVO]])
def get_report_page_for_admin(
    query_dto: ReportAdminQueryDTO,
    admin_user: User = Depends(get_current_admin),
    forum_service: ForumService = Depends()
):
    """[管理端] 分页获取聚合后的待处理举报对象"""
    page_data = forum_service.get_report_page(query_dto)
    return Result.success(data=page_data, message="获取举报列表成功")

@admin_router.get("/report/detail", response_model=Result[List[ReportDetailVO]])
def get_report_detail_for_admin(
    target_type: str = Query(..., description="目标类型: board/post/comment"),
    target_id: int = Query(..., description="目标ID"),
    status: int = Query(0, description="状态：0待处理, 1已处理, 2已驳回"),
    admin_user: User = Depends(get_current_admin),
    forum_service: ForumService = Depends()
):
    """[管理端] 获取单一目标下所有的举报记录详情"""
    details = forum_service.get_admin_report_detail(target_type, target_id, status)
    return Result.success(data=details, message="获取举报详情成功")

@admin_router.post("/report/process", response_model=Result)
def process_report_for_admin(
    dto: ReportProcessDTO,
    admin_user: User = Depends(get_current_admin), # 严格鉴权
    service: ForumService = Depends()
):
    """
    [管理端] 处理举报工单 (一键判定违规下架 或 批量驳回)
    """
    msg = service.process_reports(dto)
    return Result.success(message=msg)

@admin_router.get("/dashboard", response_model=Result[DashboardVO])
def get_dashboard_data(
    admin_user: User = Depends(get_current_admin), # 仅管理员可看大盘
    service: AdminService = Depends()
):
    """
    [管理端] 获取首页大盘统计数据
    """
    stats = service.get_dashboard_stats()
    return Result.success(data=stats, message="获取统计数据成功")

@admin_router.post("/comment/page", response_model=Result[PageData[CommentAdminVO]])
def get_comment_page_for_admin(
    dto: CommentAdminQueryDTO,
    admin_user: User = Depends(get_current_admin),
    service: ForumService = Depends()
):
    """[管理端] 分页获取评论列表 (含上下文追溯)"""
    page_data = service.get_comment_page_for_admin(dto)
    return Result.success(data=page_data, message="获取评论列表成功")

@admin_router.post("/comment/{comment_id}/status", response_model=Result)
def update_comment_status_for_admin(
    comment_id: int,
    status_dto: CommentStatusUpdateDTO,
    admin_user: User = Depends(get_current_admin),
    service: ForumService = Depends()
):
    """[管理端] 调整评论状态"""
    service.update_comment_status(comment_id, status_dto)

    # 动态生成操作成功提示语
    actions = []
    if status_dto.is_banned is not None:
        actions.append("封禁" if status_dto.is_banned else "解除封禁")
    if status_dto.is_deleted is not None:
        actions.append("标记为用户删除" if status_dto.is_deleted else "恢复用户误删")

    action_msg = "、".join(actions) if actions else "无状态修改"
    return Result.success(message=f"评论{action_msg}操作成功")

@admin_router.post("/refresh-tags")
def refresh_book_tags(
        current_user: User = Depends(get_current_admin),
        service: BookService = Depends()
):
    """
    [管理员工具] 扫描全库书籍标签并更新索引映射表
    用于在导入新书后，确保所有新标签都有对应的向量索引位。
    """
    if current_user.role != "admin":
        return Result.fail(message="只有管理员有权操作此工具")

    result = service.refresh_tag_indices()
    return Result.success(data=result, message="标签索引表更新成功")


@admin_router.post("/calculate-tfidf")
def calculate_tfidf_vectors(
        current_user: User = Depends(get_current_admin),
        service: BookService = Depends()
):
    """
    [管理员工具] 重新计算并刷新全库书籍的 TF-IDF 权重向量。
    当新增大量图书、或者手动修改过标签字典后，应执行此操作。
    """
    try:
        updated_count = service.calculate_all_books_tfidf()
        return Result.success(data={"updated_count": updated_count}, message="TF-IDF 矩阵计算并存储成功！")
    except Exception as e:
        return Result.fail(message=f"计算失败: {str(e)}")
