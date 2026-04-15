from pydantic import BaseModel, Field


class DashboardVO(BaseModel):
    """管理端大盘统计数据"""
    # 基础统计
    total_users: int = Field(default=0, description="总用户数")
    total_books: int = Field(default=0, description="总图书数")
    total_posts: int = Field(default=0, description="总帖子数")
    total_comments: int = Field(default=0, description="总评论数")

    # 待办统计
    pending_reports: int = Field(default=0, description="待处理举报数")

    # 运营数据 (可选，增加系统深度感)
    active_boards: int = Field(default=0, description="已激活的板块数")