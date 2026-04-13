from sqlmodel import Session, select, func
from app.models.user import User
from fastapi import Depends
from app.core.db import get_db
from app.models.forum import Post, Comment, PostBrowseHistory
from app.models.book import BookFavorite

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