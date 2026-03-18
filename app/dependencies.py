from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.constants import ErrorMsg
from app.core.security import decode_access_token
from app.dao.user_dao import UserDao
from app.exceptions.user_exceptions import AuthFailedException
from app.models.user import User

# HTTPBearer 规范：用于提取请求头中的 Authorization: Bearer <token>
# 加上这个后，Swagger UI 右上角会自动出现一个 "Authorize" 的锁图标
token_auth_scheme = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(token_auth_scheme),
    user_dao: UserDao = Depends()
) -> User:
    """
    核心鉴权拦截器：解析 Token，验证合法性，并查出当前操作的用户实体
    """
    if not credentials:
        raise AuthFailedException(detail=ErrorMsg.TOKEN_MISSING)

    # 1. 获取请求头里的 Token 字符串
    token = credentials.credentials

    # 2. 解码并验证 Token
    user_id_str = decode_access_token(token)
    if not user_id_str:
        raise AuthFailedException(detail=ErrorMsg.TOKEN_EXPIRED)

    # 3. 查库确认用户是否存在（防止 Token 没过期但用户已被物理删除）
    user = user_dao.get_user_by_id(int(user_id_str))
    if not user:
        raise AuthFailedException(detail=ErrorMsg.USER_NOT_FOUND)

    # 4. 鉴权通过，返回该用户对象
    return user