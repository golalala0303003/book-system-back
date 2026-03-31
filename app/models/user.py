from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime, func, Text


class User(SQLModel, table=True):
    # 表名
    __tablename__ = "user"

    # 主键
    id: Optional[int] = Field(default=None, primary_key=True)

    # 必填项
    username: str = Field(index=True, unique=True, nullable=False, max_length=50)  # 用户名
    hashed_password: str = Field(nullable=False, max_length=255)  # 加密后的密码

    # 选填项，后续编辑完善个人信息
    email: Optional[str] = Field(default=None, max_length=100)  # 邮箱
    phone: Optional[str] = Field(default=None, max_length=20)  # 电话号码
    avatar: Optional[str] = Field(default=None, max_length=255)  # 头像url
    age: Optional[int] = Field(default=None)  # 年龄
    gender: Optional[str] = Field(default="unknown", max_length=10)  # 性别
    school: Optional[str] = Field(default=None, max_length=100)  # 学校

    feature_vector: Optional[str] = Field(default=None, sa_column=Column(Text))

    # 权限与状态
    role: str = Field(default="user", max_length=20)  # 角色："user" 或 "admin"
    is_active: bool = Field(default=True)  # 账号状态，默认注册即有效

    # 时间
    create_time: datetime = Field(
        sa_column=Column(DateTime, server_default=func.now(), nullable=False)
    )
    update_time: datetime = Field(
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    )