from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

# 注册传入DTO
class UserRegisterDTO(BaseModel):
    username: str = Field(description="用户名")
    password: str = Field(description="密码")

class UserLoginDTO(BaseModel):
    """用户登录提交的数据"""
    username: str = Field(description="用户名")
    password: str = Field(description="密码")

class UserLoginVO(BaseModel):
    """用户登录成功后返回给前端的数据"""
    access_token: str = Field(description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    username: str = Field(description="用户名")
    id: int = Field(description="用户ID")
    avatar: Optional[str] = Field(description="用户头像")

class UserInfoVO(BaseModel):
    """当前登录用户全量信息 VO"""
    id: int
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    school: Optional[str] = None
    role: str
    create_time: datetime

    model_config = ConfigDict(from_attributes=True)