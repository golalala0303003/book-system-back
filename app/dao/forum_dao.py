from sqlmodel import Session, select, func, desc
from fastapi import Depends
from app.core.db import get_db
from app.models import BookFavorite, Report
from app.models.forum import Board, Post, Comment, PostVote, CommentVote, BoardFavorite, PostBrowseHistory
from app.schemas.forum_schema import PostQueryDTO, ReportAdminQueryDTO
from sqlalchemy import case

class ForumDao:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    # ---------------- 板块相关 ----------------
    def get_board_by_name(self, name: str) -> Board | None:
        statement = select(Board).where(Board.name == name)
        return self.db.exec(statement).first()

    def get_board_by_id(self, board_id: int) -> Board | None:
        return self.db.get(Board, board_id)

    def get_active_boards(self, limit) -> list[Board]:
        """获取所有未被隐藏的板块"""
        statement = select(Board).where(Board.is_active == True).order_by(Board.post_count.desc()).limit(limit)
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

    def favorite_board(self, board_favorite: BoardFavorite) -> BoardFavorite:
        self.db.add(board_favorite)
        self.db.commit()
        self.db.refresh(board_favorite)
        return board_favorite

    def get_board_by_keyword(self, key_word, limit):
        search_str = f"%{key_word}%"
        statement = select(Board).where(Board.is_active == True)
        statement = statement.where(Board.name.like(search_str))
        statement = statement.limit(limit)
        boards = self.db.exec(statement).all()
        return boards

    def get_favorite_board(self, user_id: int, board_id: int) -> BoardFavorite | None:
        statement = select(BoardFavorite).where(BoardFavorite.user_id == user_id,
                                                BoardFavorite.board_id == board_id,
                                                Board.is_active == True)
        return self.db.exec(statement).first()

    def delete_favorite_board(self, favorite_record):
        self.db.delete(favorite_record)
        self.db.commit()

    def get_favorite_board_ids_by_user_id(self, limit: int, user_id: int) -> list[int] | None:
        statement = (select(BoardFavorite.board_id)
                     .where(BoardFavorite.user_id == user_id)
                     .limit(limit))
        return self.db.exec(statement).all()

    def get_boards_by_ids(self, ids):
        statement = (select(Board)
                     .where(Board.id.in_(ids),
                                        Board.is_active == True)
                     .order_by(Board.post_count.desc()))
        return self.db.exec(statement).all()


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

    def get_post_browse_ids(self, user_id, page, size):
        """获取用户浏览记录的帖子ID，同时过滤掉已删除的帖子"""
        statement = (
            select(PostBrowseHistory.post_id)
            .join(Post, PostBrowseHistory.post_id == Post.id)  # 关联帖子表
            .where(
                PostBrowseHistory.user_id == user_id,
                Post.is_deleted == False
            )
            .order_by(PostBrowseHistory.last_view_time.desc())
        )

        count_statement = select(func.count()).select_from(statement.subquery())
        total = self.db.exec(count_statement).one()

        statement = statement.offset((page - 1) * size).limit(size)
        return total, self.db.exec(statement).all()

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

    def get_posts_by_book_ids(self, book_ids: list[int], limit: int) -> list[Post]:
        """根据关联的图书ID集合批量查询帖子，按浏览量降序"""
        if not book_ids:
            return []
        statement = (
            select(Post)
            .where(Post.book_id.in_(book_ids))
            .where(Post.is_deleted == False)
            .order_by(Post.view_count.desc())
            .limit(limit)
        )
        return self.db.exec(statement).all()

    def get_hot_posts_exclude_ids(self, exclude_ids: list[int], limit: int) -> list[Post]:
        """获取全站热门帖子（按浏览量降序），并排除指定的帖子ID"""
        if limit <= 0:
            return []
        statement = select(Post).where(Post.is_deleted == False)

        if exclude_ids:
            statement = statement.where(Post.id.not_in(exclude_ids))

        statement = statement.order_by(Post.view_count.desc()).limit(limit)
        return self.db.exec(statement).all()

    def get_unified_recommend_posts_page(self, book_ids: list[int], page: int, size: int) -> tuple[int, list[Post]]:
        """
        统一推荐查询：优先展示 book_id 在推荐列表中的帖子，其次展示全站热门帖子，支持标准分页
        """
        # 1. 查询总条数 (就是全站所有未删除的帖子总数)
        count_stmt = select(func.count()).select_from(Post).where(Post.is_deleted == False)
        total = self.db.exec(count_stmt).one()

        # 2. 构建分页查询
        statement = select(Post).where(Post.is_deleted == False)

        if book_ids:
            # 核心魔法：构建一个虚拟的排序权重列
            # 如果帖子的 book_id 在推荐书单里，权重为 1，否则为 0
            is_recommended = case(
                (Post.book_id.in_(book_ids), 1),
                else_=0
            )
            # 排序规则：先按权重排（推荐的在前），权重相同的按浏览量排，最后按时间兜底
            statement = statement.order_by(
                is_recommended.desc(),
                Post.view_count.desc(),
                Post.create_time.desc()
            )
        else:
            # 如果没有推荐书单，直接按浏览量排序
            statement = statement.order_by(Post.view_count.desc(), Post.create_time.desc())

        # 标准分页
        statement = statement.offset((page - 1) * size).limit(size)
        records = self.db.exec(statement).all()

        return total, records

    def record_browse_history(self, user_id, post_id):
        """记录浏览历史：存在则更新次数和时间，不存在则新增"""
        statement = select(PostBrowseHistory).where(
            PostBrowseHistory.user_id == user_id,
            PostBrowseHistory.post_id == post_id
        )
        history = self.db.exec(statement).first()

        if history:
            history.view_times += 1
            self.db.add(history)
        else:
            new_history = PostBrowseHistory(user_id=user_id, post_id=post_id)
            self.db.add(new_history)

        self.db.commit()

    def create_report(self, report: Report) -> Report:
        """创建一条举报记录"""
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def get_aggregated_reports_page(self, dto: ReportAdminQueryDTO) -> tuple[int, list]:
        """
        [管理端] 聚合查询：按 target_type 和 target_id 分组统计
        """
        # 1. 基础过滤条件
        base_stmt = select(Report.target_type, Report.target_id).where(Report.status == dto.status)
        if dto.target_type:
            base_stmt = base_stmt.where(Report.target_type == dto.target_type)

        # 2. 计算总的分组数 (用于完美分页)
        group_subquery = base_stmt.group_by(Report.target_type, Report.target_id).subquery()
        count_stmt = select(func.count()).select_from(group_subquery)
        total = self.db.exec(count_stmt).one()

        # 3. 提取聚合字段并按被举报次数倒序
        stmt = select(
            Report.target_type,
            Report.target_id,
            func.count(Report.id).label("report_count"),
            func.max(Report.create_time).label("latest_report_time")
        ).where(Report.status == dto.status)

        if dto.target_type:
            stmt = stmt.where(Report.target_type == dto.target_type)

        stmt = stmt.group_by(Report.target_type, Report.target_id)
        stmt = stmt.order_by(desc("report_count"), desc("latest_report_time"))

        # 4. 执行分页
        stmt = stmt.offset((dto.page - 1) * dto.size).limit(dto.size)
        records = self.db.exec(stmt).all()

        # records 返回的是 tuple 列表: (target_type, target_id, report_count, latest_report_time)
        return total, records

    def get_report_details(self, target_type: str, target_id: int, status: int) -> list[Report]:
        """
        [管理端] 获取单一目标的所有详细举报记录
        """
        stmt = select(Report).where(
            Report.target_type == target_type,
            Report.target_id == target_id,
            Report.status == status
        ).order_by(Report.create_time.desc())
        return self.db.exec(stmt).all()

    def update_reports_status_batch(self, target_type: str, target_id: int, new_status: int):
        """
        [管理端] 批量更新针对某一目标的待处理举报工单
        """
        # 找到该目标下所有状态为 0 (待处理) 的举报单
        statement = select(Report).where(
            Report.target_type == target_type,
            Report.target_id == target_id,
            Report.status == 0
        )
        reports = self.db.exec(statement).all()

        for report in reports:
            report.status = new_status
            self.db.add(report)

        # 这里先不 commit，由 Service 统一提交事务
        self.db.flush()

    def get_forum_stats(self) -> dict:
        """获取论坛相关统计数据"""
        # 总帖子数 (排除逻辑删除)
        post_count = self.db.exec(select(func.count(Post.id)).where(Post.is_deleted == False)).one()
        # 总评论数 (排除逻辑删除)
        comment_count = self.db.exec(select(func.count(Comment.id)).where(Comment.is_deleted == False)).one()
        # 有效板块数
        board_count = self.db.exec(select(func.count(Board.id)).where(Board.is_active == True)).one()
        # 待处理举报数 (status == 0)
        pending_reports = self.db.exec(select(func.count(Report.id)).where(Report.status == 0)).one()

        return {
            "post_count": post_count,
            "comment_count": comment_count,
            "board_count": board_count,
            "pending_reports": pending_reports
        }