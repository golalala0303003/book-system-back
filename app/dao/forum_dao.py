from sqlmodel import Session, select, func
from fastapi import Depends
from app.core.db import get_db
from app.models.forum import Board, Post, Comment, PostVote, CommentVote
from app.schemas.forum_schema import PostQueryDTO


class ForumDao:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    # ---------------- 板块相关 ----------------
    def get_board_by_name(self, name: str) -> Board | None:
        statement = select(Board).where(Board.name == name)
        return self.db.exec(statement).first()

    def get_board_by_id(self, board_id: int) -> Board | None:
        return self.db.get(Board, board_id)

    def get_active_boards(self) -> list[Board]:
        """获取所有未被隐藏的板块"""
        statement = select(Board).where(Board.is_active == True).order_by(Board.id)
        return self.db.exec(statement).all()

    def create_board(self, board: Board) -> Board:
        self.db.add(board)
        self.db.commit()
        self.db.refresh(board)
        return board

    def update_board(self, board: Board) -> Board:
        self.db.add(board)
        self.db.commit()
        self.db.refresh(board)
        return board

    # ---------------- 帖子相关 ----------------
    def get_post_by_id(self, post_id: int) -> Post | None:
        statement = select(Post).where(Post.id == post_id, Post.is_deleted == False)
        return self.db.exec(statement).first()

    def create_post(self, post: Post) -> Post:
        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)
        return post

    def update_post(self, post: Post) -> Post:
        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)
        return post

    def increment_view_count(self, post_id: int):
        """让帖子的浏览量 +1"""
        post = self.get_post_by_id(post_id)
        if post:
            post.view_count += 1
            self.db.add(post)
            self.db.commit()

    def get_posts_page(self, dto: "PostQueryDTO") -> tuple[int, list[Post]]:
        """复杂分页查询，返回 (总条数, 帖子列表)"""
        # 基础查询条件（排除已删除的）
        statement = select(Post).where(Post.is_deleted == False)

        # 动态追加筛选条件
        if dto.board_id:
            statement = statement.where(Post.board_id == dto.board_id)
        if dto.book_id:
            statement = statement.where(Post.book_id == dto.book_id)
        if dto.keyword:
            statement = statement.where(Post.title.like(f"%{dto.keyword}%"))
        if dto.user_id:
            statement = statement.where(Post.user_id == dto.user_id)

        # 查出符合条件的总条数
        count_statement = select(func.count()).select_from(statement.subquery())
        total = self.db.exec(count_statement).one()

        # 动态排序
        if dto.sort_by == "upvote":
            # 按点赞数倒序。如果有两个帖子点赞数一样，再按时间倒序
            statement = statement.order_by(Post.upvote_count.desc(), Post.create_time.desc())
        elif dto.sort_by == "view":
            # 按浏览量倒序。
            statement = statement.order_by(Post.view_count.desc(), Post.create_time.desc())
        else:
            # 默认情况 (dto.sort_by == "time" 或其他值)，直接按时间倒序兜底
            statement = statement.order_by(Post.create_time.desc())

        # 执行分页并拉取数据
        statement = statement.offset((dto.page - 1) * dto.size).limit(dto.size)
        records = self.db.exec(statement).all()

        return total, records

    # ---------------- 评论相关 ----------------
    def get_comment_by_id(self, comment_id: int) -> Comment | None:
        statement = select(Comment).where(Comment.id == comment_id, Comment.is_deleted == False)
        return self.db.exec(statement).first()

    def create_comment(self, comment: Comment) -> Comment:
        self.db.add(comment)
        self.db.commit()
        self.db.refresh(comment)
        return comment

    def update_comment(self, comment: Comment) -> Comment:
        self.db.add(comment)
        self.db.commit()
        self.db.refresh(comment)
        return comment

    def get_comments_by_post(self, post_id: int) -> list[Comment]:
        """获取某个帖子下的所有未删除评论，按时间升序排列 (老的在上面)"""
        statement = select(Comment).where(
            Comment.post_id == post_id,
            Comment.is_deleted == False
        ).order_by(Comment.create_time.asc())
        return self.db.exec(statement).all()

    # ---------------- 互动/评价相关 ----------------
    def get_post_vote(self, user_id: int, post_id: int) -> PostVote | None:
        """查询用户对某个帖子是否已经表过态"""
        statement = select(PostVote).where(
            PostVote.user_id == user_id,
            PostVote.post_id == post_id
        )
        return self.db.exec(statement).first()

    def get_comment_vote(self, user_id: int, comment_id: int) -> CommentVote | None:
        """查询用户对某条评论是否已经表过态"""
        statement = select(CommentVote).where(
            CommentVote.user_id == user_id,
            CommentVote.comment_id == comment_id
        )
        return self.db.exec(statement).first()

    # ---------------- 互动/评价 批量查询补充 ----------------
    def get_user_post_votes_batch(self, user_id: int, post_ids: list[int]) -> dict[int, int]:
        """批量获取用户对一批帖子的点赞状态，返回格式: {post_id: vote_type}"""
        if not post_ids:
            return {}
        statement = select(PostVote).where(
            PostVote.user_id == user_id,
            PostVote.post_id.in_(post_ids)
        )
        votes = self.db.exec(statement).all()
        return {v.post_id: v.vote_type for v in votes}

    def get_user_comment_votes_batch(self, user_id: int, comment_ids: list[int]) -> dict[int, int]:
        """批量获取用户对一批评论的点赞状态，返回格式: {comment_id: vote_type}"""
        if not comment_ids:
            return {}
        statement = select(CommentVote).where(
            CommentVote.user_id == user_id,
            CommentVote.comment_id.in_(comment_ids)
        )
        votes = self.db.exec(statement).all()
        return {v.comment_id: v.vote_type for v in votes}