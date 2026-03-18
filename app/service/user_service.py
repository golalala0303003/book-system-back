from sqlmodel import Session
from app.schemas.user_schema import UserRegisterDTO, UserLoginDTO, UserLoginVO
from app.models.user import User
from app.dao.user_dao import UserDao
from app.core.security import get_password_hash, verify_password, create_access_token
from fastapi import Depends

class UserService:
    def __init__(self, dao: UserDao = Depends()):
        self.dao = dao


    def register(self, user_dto: UserRegisterDTO) -> bool:
        # TODO 校验逻辑 (如查重)

        # 组装实体
        new_user = User(
            username=user_dto.username,
            hashed_password=get_password_hash(user_dto.password)
        )

        self.dao.create_user(new_user)
        return True


    def login(self, login_dto: UserLoginDTO) -> tuple[bool, str | UserLoginVO]:
        """
        用户登录业务逻辑
        返回: (是否成功, 错误信息字符串 或 UserLoginVO对象)
        """
        # 1. 查找用户是否存在
        user = self.dao.get_user_by_username(login_dto.username)
        if not user:
            return False, "用户名或密码错误"

        # 2. 校验密码是否匹配
        if not verify_password(login_dto.password, user.hashed_password):
            return False, "用户名或密码错误"

        # 3. 登录成功，签发 JWT Token
        # 注意：我们将用户 ID 作为 sub 载荷
        access_token = create_access_token(subject=user.id)

        # 4. 封装返回对象 (VO)
        login_vo = UserLoginVO(
            access_token=access_token,
            id=user.id,
            username=user.username
        )

        return True, login_vo
