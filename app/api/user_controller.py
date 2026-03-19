from fastapi import APIRouter, Depends

from app.core.constants import SuccessMsg
from app.dependencies import get_current_user
from app.models import User
from app.schemas.result import Result
from app.schemas.user_schema import UserRegisterDTO, UserLoginDTO, UserLoginVO, UserInfoVO
from app.service.user_service import UserService


router = APIRouter(prefix="/user", tags=["用户模块"])

@router.post("/register")
def register(user_dto: UserRegisterDTO, service: UserService = Depends()):
    service.register(user_dto)
    return Result.success(message=SuccessMsg.REGISTER_SUCCESS)


@router.post("/login")
def login(login_dto: UserLoginDTO, service: UserService = Depends()):
    # TODO
    result_data = service.login(login_dto)
    return Result.success(data=result_data, message="登录成功")


@router.get("/me")
def get_user_info(current_user: User = Depends(get_current_user)):
    """
    获取当前登录用户的详细信息
    """
    user_info = UserInfoVO.model_validate(current_user)
    return Result.success(data=user_info, message="获取用户信息成功")
