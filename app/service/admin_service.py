from fastapi import Depends
from app.dao.user_dao import UserDao
from app.dao.book_dao import BookDao
from app.dao.forum_dao import ForumDao
from app.schemas.admin_schema import DashboardVO


class AdminService:
    def __init__(
            self,
            user_dao: UserDao = Depends(),
            book_dao: BookDao = Depends(),
            forum_dao: ForumDao = Depends()
    ):
        self.user_dao = user_dao
        self.book_dao = book_dao
        self.forum_dao = forum_dao

    def get_dashboard_stats(self) -> DashboardVO:
        """聚合所有后台统计数据"""
        forum_stats = self.forum_dao.get_forum_stats()

        return DashboardVO(
            total_users=self.user_dao.get_total_users(),
            total_books=self.book_dao.get_total_books(),
            total_posts=forum_stats["post_count"],
            total_comments=forum_stats["comment_count"],
            pending_reports=forum_stats["pending_reports"],
            active_boards=forum_stats["board_count"]
        )