from typing import Optional

from sqlmodel import Session

from app.exceptions.user_exceptions import UserNotFoundException, IncorrectPasswordException, UserAlreadyExistsException
from app.schemas.user_schema import UserRegisterDTO, UserLoginDTO, UserLoginVO, UserUpdateDTO, UserInfoVO, UserStatsVO
from app.models.user import User
from app.dao.user_dao import UserDao
from app.core.security import get_password_hash, verify_password, create_access_token
from fastapi import Depends

class UserService:
    def __init__(self, dao: UserDao = Depends()):
        self.dao = dao


    def register(self, user_dto: UserRegisterDTO) -> bool:
        user = self.dao.get_user_by_username(user_dto.username)
        if user:
            raise UserAlreadyExistsException()

        # 组装实体
        new_user = User(
            username=user_dto.username,
            hashed_password=get_password_hash(user_dto.password)
        )

        self.dao.create_user(new_user)

        return True


    def login(self, login_dto: UserLoginDTO) -> UserLoginVO:
        """
        用户登录
        """
        # 1. 查找用户是否存在
        user = self.dao.get_user_by_username(login_dto.username)
        if not user:
            raise UserNotFoundException()

        # 2. 校验密码是否匹配
        if not verify_password(login_dto.password, user.hashed_password):
            raise IncorrectPasswordException()

        # 3. 登录成功，签发 JWT Token
        # 注意：我们将用户 ID 作为 sub 载荷
        access_token = create_access_token(subject=user.id)

        # 4. 封装返回对象 (VO)
        login_vo = UserLoginVO(
            access_token=access_token,
            id=user.id,
            username=user.username,
            avatar=user.avatar,
        )

        return login_vo

    def update_user(self, current_user: User, update_dto: UserUpdateDTO) -> UserInfoVO:
        update_data = update_dto.model_dump(exclude_unset=True)

        if "username" in update_data and update_data["username"] != current_user.username:
            existing_user = self.dao.get_user_by_username(update_data["username"])
            if existing_user:
                raise UserAlreadyExistsException()

        for key, value in update_data.items():
            setattr(current_user, key, value)
        current_user = self.dao.update_user(current_user)
        user_info = UserInfoVO.model_validate(current_user)
        return user_info

    def get_user_profile(self, user_id, current_user: Optional[User]):
        user = self.dao.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundException()
        user_info = UserInfoVO.model_validate(user)

        is_self = (current_user is not None) and (user_id == current_user.id)

        if not is_self:
            # 隐藏手机号
            if user_info.phone and len(user_info.phone) >= 11:
                user_info.phone = f"{user_info.phone[:3]}****{user_info.phone[-4:]}"
            elif user_info.phone:
                user_info.phone = "***"

            # 隐藏邮箱
            if user_info.email and "@" in user_info.email:
                name, domain = user_info.email.split("@", 1)
                if len(name) > 2:
                    user_info.email = f"{name[:2]}***@{domain}"
                else:
                    user_info.email = f"***@{domain}"
            elif user_info.email:
                user_info.email = "***"

        return user_info

    def get_user_stats(self, user_id: int) -> UserStatsVO:
        """
        获取用户公开的统计面板数据
        """
        # 1. 严格校验用户有效性
        user = self.dao.get_user_by_id(user_id)  # 假设你 UserDao 有这个基础查询方法
        if not user:
            raise UserNotFoundException()

        # 2. 调用 DAO 执行底层聚合
        stats_dict = self.dao.get_user_statistics(user_id)

        # 3. 字典解包并组装为响应 VO
        return UserStatsVO(**stats_dict)