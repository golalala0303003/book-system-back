from fastapi import APIRouter, Depends

from app.core.constants import SuccessMsg
from app.dependencies import get_current_user
from app.models import User
from app.schemas.result import Result
from app.schemas.user_schema import UserRegisterDTO, UserLoginDTO, UserLoginVO, UserInfoVO, UserUpdateDTO
from app.service.user_service import UserService


router = APIRouter(prefix="/user", tags=["用户模块"])

@router.post("/register")
def register(user_dto: UserRegisterDTO, service: UserService = Depends()):
    service.register(user_dto)
    return Result.success(message=SuccessMsg.REGISTER_SUCCESS)


@router.post("/login")
def login(login_dto: UserLoginDTO, service: UserService = Depends()):
    result_data = service.login(login_dto)
    return Result.success(data=result_data, message=SuccessMsg.LOGIN_SUCCESS)


@router.get("/me")
def get_user_info(current_user: User = Depends(get_current_user)):
    """
    获取当前登录用户的详细信息,只能获取自己的
    """
    user_info = UserInfoVO.model_validate(current_user)
    return Result.success(data=user_info, message=SuccessMsg.GET_USER_INFO_SUCCESS)

@router.get("/profile/{user_id}")
def get_user_profile(user_id: int, service: UserService = Depends(), current_user: User = Depends(get_current_user)):
    """
    获取任意id用户的用户资料
    """
    user_info = service.get_user_profile(user_id, current_user.id)
    return Result.success(data=user_info, message=SuccessMsg.GET_USER_INFO_SUCCESS)

@router.post("/update")
def update_user(
        update_dto: UserUpdateDTO,
        current_user: User = Depends(get_current_user),
        service: UserService = Depends()
):
    """
    更新用户信息，至少传一个要更新的参数
    """
    user_info = service.update_user(current_user, update_dto)
    return Result.success(data=user_info, message=SuccessMsg.UPDATE_USER_SUCCESS)
