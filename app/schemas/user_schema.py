from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Optional
from datetime import datetime

from app.exceptions.user_exceptions import AtLeastOneFieldException


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

# 更新信息DTO
class UserUpdateDTO(BaseModel):
    username: Optional[str] = Field(default=None, description="用户名", max_length=50)
    email: Optional[str] = Field(default=None, description="邮箱", max_length=100)
    phone: Optional[str] = Field(default=None, description="电话号码", max_length=20)
    avatar: Optional[str] = Field(default=None, description="头像url", max_length=255)
    age: Optional[int] = Field(default=None, description="年龄")
    gender: Optional[str] = Field(default=None, description="性别", max_length=10)
    school: Optional[str] = Field(default=None, description="学校", max_length=100)

    @model_validator(mode='after')
    def check_at_least_one_field(self):
        # self.model_dump(exclude_unset=True) 会过滤掉前端没传的字段
        # 如果过滤后是个空字典，说明前端什么都没传
        if not self.model_dump(exclude_unset=True):
            raise AtLeastOneFieldException()
        return self