from typing import List

from fastapi import APIRouter, Depends, Query

from app.core.constants import SuccessMsg
from app.dependencies import get_current_user, get_current_user_optional, get_current_admin
from app.models import User
from app.schemas.admin_schema import DashboardVO
from app.schemas.book_schema import BookAdminQueryDTO, BookAdminVO, BookStatusUpdateDTO, BookCreateDTO, BookUpdateDTO
from app.schemas.forum_schema import ReportAggregatedVO, ReportAdminQueryDTO, ReportDetailVO, ReportProcessDTO
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