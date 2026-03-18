import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Any
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from app.core.config import settings

# 密码哈希配置
password_hash = PasswordHash((Argon2Hasher(),))


def get_password_hash(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


# JWT 逻辑配置
def create_access_token(subject: str | Any, expires_delta: Optional[timedelta] = None) -> str:
    """
    生成 JWT Access Token
    :param subject: 载荷(Payload)中的主体，通常存放用户 ID
    :param expires_delta: 过期时间增量
    :return: 加密后的字符串
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    # 构造载荷 (Payload)
    # sub (subject): 代表该 Token 的所有者
    # exp (expiration time): 过期时间戳
    # iat (issued at): 签发时间
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    }

    # 使用 SECRET_KEY 和指定算法进行加密
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[str]:
    """
    解密并验证 JWT Token
    :param token: 待验证的字符串
    :return: 成功返回 sub (用户ID)，失败返回 None
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload.get("sub")
    except (jwt.PyJWTError, AttributeError):
        # 包含过期、签名错误、格式错误等所有 JWT 相关异常
        return None