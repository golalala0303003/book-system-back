from fastapi import APIRouter, Depends

from app.core.constants import SuccessMsg
from app.dependencies import get_current_user, get_current_user_optional, get_current_admin
from app.models import User
from app.schemas.result import Result, PageData
from app.schemas.user_schema import UserAdminVO, UserAdminQueryDTO, UserStatusUpdateDTO
from app.service.user_service import UserService


admin_router = APIRouter(prefix="/admin", tags=["后台管理模块"])


@admin_router.post("/user/page", response_model=Result[PageData[UserAdminVO]])
def get_user_page_for_admin(
    query_dto: UserAdminQueryDTO,
    admin_user: User = Depends(get_current_admin),
    service: UserService = Depends()
):
    """
    [管理端] 分页获取用户列表 (支持按用户名、状态筛选)
    """
    page_data = service.get_admin_user_page(query_dto)
    return Result.success(data=page_data, message="获取用户列表成功")


@admin_router.post("/user/{user_id}/status", response_model=Result)
def update_user_status(
        user_id: int,
        status_dto: UserStatusUpdateDTO,
        admin_user: User = Depends(get_current_admin),
        service: UserService = Depends()
):
    """
    [管理端] 调整用户账号状态 (封禁/解封)
    """
    service.update_user_status(user_id, status_dto)

    action_msg = "解封" if status_dto.is_active else "封禁"
    return Result.success(message=f"用户{action_msg}操作成功")