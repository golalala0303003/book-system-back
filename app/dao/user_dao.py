from sqlmodel import Session, select, func
from app.models.user import User
from fastapi import Depends
from app.core.db import get_db
from app.models.forum import Post, Comment, PostBrowseHistory
from app.models.book import BookFavorite
from app.schemas.user_schema import UserAdminQueryDTO


class UserDao:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db


    def get_user_by_username(self, username: str) -> User | None:
        statement = select(User).where(User.username == username)
        return self.db.exec(statement).first()


    def get_user_by_id(self, user_id: int) -> User | None:
        statement = select(User).where(User.id == user_id)
        return self.db.exec(statement).first()


    def create_user(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_user(self, current_user):
        self.db.add(current_user)
        self.db.commit()
        self.db.refresh(current_user)
        return current_user

    def get_user_statistics(self, user_id: int) -> dict:
        """
        实时聚合查询指定用户的各项统计数据
        """
        # 1. 发帖总数
        post_count_stmt = select(func.count(Post.id)).where(
            Post.user_id == user_id,
            Post.is_deleted == False
        )
        post_count = self.db.exec(post_count_stmt).one_or_none() or 0

        # 2. 收藏/阅读图书总数
        fav_book_count_stmt = select(func.count(BookFavorite.id)).where(
            BookFavorite.user_id == user_id
        )
        fav_book_count = self.db.exec(fav_book_count_stmt).one_or_none() or 0

        # 3. 帖子获赞数 (SUM 处理)
        post_upvote_stmt = select(func.sum(Post.upvote_count)).where(
            Post.user_id == user_id,
            Post.is_deleted == False
        )
        post_upvotes = self.db.exec(post_upvote_stmt).one_or_none() or 0

        # 4. 评论获赞数 (SUM 处理)
        comment_upvote_stmt = select(func.sum(Comment.upvote_count)).where(
            Comment.user_id == user_id,
            Comment.is_deleted == False
        )
        comment_upvotes = self.db.exec(comment_upvote_stmt).one_or_none() or 0

        # 5. 浏览过的帖子总数
        viewed_post_stmt = select(func.count(PostBrowseHistory.id)).where(
            PostBrowseHistory.user_id == user_id
        )
        viewed_post_count = self.db.exec(viewed_post_stmt).one_or_none() or 0

        # 6. 参与评论的总数
        comment_count_stmt = select(func.count(Comment.id)).where(
            Comment.user_id == user_id,
            Comment.is_deleted == False
        )
        comment_count = self.db.exec(comment_count_stmt).one_or_none() or 0

        # 返回字典供 Service 层组装
        return {
            "post_count": post_count,
            "favorite_book_count": fav_book_count,
            "received_upvote_count": post_upvotes + comment_upvotes,
            "viewed_post_count": viewed_post_count,
            "comment_count": comment_count
        }

    def get_users_page_for_admin(self, dto: UserAdminQueryDTO) -> tuple[int, list[User]]:
        """
        [管理端] 分页条件查询用户列表 (包含动态排序)
        """
        statement = select(User)

        # 1. 动态拼接条件
        if dto.keyword:
            statement = statement.where(User.username.like(f"%{dto.keyword}%"))

        if dto.is_active is not None:
            statement = statement.where(User.is_active == dto.is_active)

        # 2. 统计符合条件的总数
        count_statement = select(func.count()).select_from(statement.subquery())
        total = self.db.exec(count_statement).one()

        # 3. 动态拼接排序逻辑 (核心修改点)
        # 定义允许排序的字段白名单，防止异常字段注入
        sort_mapping = {
            "create_time": User.create_time,
            "id": User.id,
            "username": User.username
        }

        # 获取目标排序字段，如果前端传了不认识的字段，则回退到 create_time
        sort_column = sort_mapping.get(dto.sort_by, User.create_time)

        # 根据方向应用排序
        if dto.sort_order.lower() == "asc":
            statement = statement.order_by(sort_column.asc())
        else:
            statement = statement.order_by(sort_column.desc())

        # 4. 按注册时间倒序排，并进行分页
        statement = statement.offset((dto.page - 1) * dto.size).limit(dto.size)

        records = self.db.exec(statement).all()
        return total, records

    def get_total_users(self) -> int:
        """获取总用户数"""
        statement = select(func.count(User.id))
        return self.db.exec(statement).one()