from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime, func


class Report(SQLModel, table=True):
    __tablename__ = "report"

    id: Optional[int] = Field(default=None, primary_key=True)

    # 举报人
    user_id: int = Field(index=True, description="发起举报的用户ID")

    # 目标信息
    target_type: str = Field(index=True, max_length=20, description="目标类型：'board', 'post', 'comment'")
    target_id: int = Field(index=True, description="具体的目标对象ID")

    # 举报内容
    reason: str = Field(max_length=500, description="具体的举报原因或详情")

    # 状态 0=待处理, 1=举报成立并已处理, 2=举报不成立已驳回
    status: int = Field(default=0, index=True, description="处理状态")

    # 处理备注
    process_remark: Optional[str] = Field(default=None, max_length=500, description="管理员的处理理由/驳回理由")

    # 时间
    create_time: datetime = Field(
        sa_column=Column(DateTime, server_default=func.now(), nullable=False)
    )
    update_time: datetime = Field(
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    )