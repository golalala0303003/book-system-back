from fastapi import Depends
from app.dao.forum_dao import ForumDao
from app.dao.user_dao import UserDao
from app.exceptions.user_exceptions import UserNotPermittedException, UserNotFoundException
from app.models import Report
from app.models.user import User
from app.models.forum import Board, Post, Comment, CommentVote, PostVote, BoardFavorite
from app.schemas.forum_schema import BoardCreateDTO, BoardVO, PostCreateDTO, PostVO, PostQueryDTO, PostUpdateDTO, \
    CommentCreateDTO, CommentVO, RootCommentVO, CommentVoteDTO, PostVoteDTO, BoardFavoriteDTO, BoardSuggestVO, \
    ReportCreateDTO, ReportAdminQueryDTO, ReportAggregatedVO, ReportDetailVO, ReportProcessDTO, BoardAdminVO, \
    BoardAdminQueryDTO, BoardStatusUpdateDTO
from app.exceptions.forum_exceptions import BoardAlreadyExistsException, BoardNotExistsException, \
    PostNotExistsException, CommentNotExistsException, InvalidCommentLevelException, IllegalReportTypeException, \
    BoardHasBeenBannedException
from app.schemas.result import PageData
from collections import defaultdict
from typing import Optional

from app.service.book_service import BookService
from app.service.user_service import UserService
import app.core.utils as utils

class ForumService:
    def __init__(self, dao: ForumDao = Depends(), user_dao: UserDao = Depends()):
        self.forum_dao = dao
        self.user_dao = user_dao

    # ---------------- 板块业务 ----------------
    def create_board(self, dto: BoardCreateDTO, current_user: User) -> BoardVO:
        # 校验板块名是否重复
        existing_board = self.forum_dao.get_board_by_name(dto.name)
        if existing_board:
            raise BoardAlreadyExistsException()

        # 构造实体
        new_board = Board(
            name=dto.name,
            description=dto.description,
            cover_url=dto.cover_url,
            creator_id=current_user.id
        )

        # 保存入库
        saved_board = self.forum_dao.create_board(new_board)

        # 返回 VO
        return BoardVO.model_validate(saved_board)

    def get_board_detail(self, board_id, current_user: Optional[User]) -> BoardVO:
        board = self.forum_dao.get_board_by_id(board_id)
        if not board:
            raise BoardNotExistsException()
        if not board.is_active:
            raise BoardHasBeenBannedException()
        board_vo = BoardVO.model_validate(board)
        if current_user:
            board_favorite = self.forum_dao.get_favorite_board(current_user.id, board.id)
            if board_favorite:
                board_vo.fav_status = True
            else:
                board_vo.fav_status = False
        else:
            board_vo.fav_status = False

        return board_vo

    def delete_board(self, board_id: int, current_user: User):
        # 权限校验:只允许管理员删除
        if current_user.role != "admin":
            raise UserNotPermittedException()

        # 检查板块是否存在
        board = self.forum_dao.get_board_by_id(board_id)
        if not board:
            raise BoardNotExistsException()

        # 逻辑删除（隐藏）
        board.is_active = False
        self.forum_dao.update_board(board)
        return True

    def get_all_boards(self, limit) -> list[BoardVO]:
        boards = self.forum_dao.get_active_boards(limit)
        return [BoardVO.model_validate(b) for b in boards]

    def get_board_page_for_admin(self, dto: BoardAdminQueryDTO) -> PageData[BoardAdminVO]:
        # 调 DAO 查数据
        total, records = self.forum_dao.get_board_page_for_admin(dto)
        vo_list = [BoardAdminVO.model_validate(record) for record in records]

        # 组装
        return PageData(
            total=total,
            page=dto.page,
            size=dto.size,
            records=vo_list
        )

    def update_board_status(self, board_id: int, status_dto: BoardStatusUpdateDTO) -> None:
        """
        [管理端] 调整板块状态 (封禁/解封)
        """
        # 1. 查找板块是否存在
        board = self.forum_dao.get_board_by_id(board_id)
        if not board:
            raise BoardNotExistsException()

        # 2. 如果状态没有改变，直接返回
        if board.is_active == status_dto.is_active:
            return

        # 3. 更新状态并保存到数据库
        board.is_active = status_dto.is_active
        self.forum_dao.update_board(board)

    def get_favorite_board_list(self, limit: int, current_user: User):
        # 没有登录的时候返回空
        if not current_user:
            return []
        else:
            # 获取用户收藏的所有板块的id
            ids = self.forum_dao.get_favorite_board_ids_by_user_id(limit, current_user.id)
            # 根据id批量查询板块
            boards = self.forum_dao.get_boards_by_ids(ids)
            return [BoardVO.model_validate(b) for b in boards]

    def get_board_suggest(self, key_word, limit):
        boards = self.forum_dao.get_board_by_keyword(key_word, limit)
        vo_list = [BoardSuggestVO.model_validate(b) for b in boards]
        return vo_list

    def favorite_board(self, dto: BoardFavoriteDTO, current_user: User):
        board = self.forum_dao.get_board_by_id(dto.board_id)
        if not board or not board.is_active:
            raise BoardNotExistsException()
        # 收藏
        if dto.status == 1:
            favorite_record = self.forum_dao.get_favorite_board(current_user.id, dto.board_id)
            if favorite_record:
                return
            new_board_favorite = BoardFavorite(
                user_id=current_user.id,
                board_id=dto.board_id,
            )
            self.forum_dao.favorite_board(new_board_favorite)
        else:
            favorite_record = self.forum_dao.get_favorite_board(current_user.id, dto.board_id)
            if not favorite_record:
                return
            self.forum_dao.delete_favorite_board(favorite_record)

    # ---------------- 帖子业务 ----------------
    def create_post(self, dto: PostCreateDTO, current_user: User) -> PostVO:
        # 校验板块是否存在且处于激活状态
        board = self.forum_dao.get_board_by_id(dto.board_id)
        if not board or not board.is_active:
            raise BoardNotExistsException()

        # TODO 如果传了 book_id，校验图书是否存在

        # 构造帖子实体
        new_post = Post(
            title=dto.title,
            content=dto.content,
            cover_image=dto.cover_image,
            board_id=dto.board_id,
            book_id=dto.book_id,
            user_id=current_user.id
        )

        # 保存入库
        saved_post = self.forum_dao.create_post(new_post)
        return PostVO.model_validate(saved_post)

    def delete_post(self, post_id: int, current_user: User):
        # 查出帖子
        post = self.forum_dao.get_post_by_id(post_id)
        if not post:
            raise PostNotExistsException()

        # 权限校验：发帖人本人 或者 管理员可以删除
        if post.user_id != current_user.id and current_user.role != "admin":
            raise UserNotPermittedException()

        # 逻辑删除
        post.is_deleted = True
        self.forum_dao.update_post(post)

        # TODO 删除关联的评论
        return True

    def get_post_detail(self, post_id: int, record_view: bool, current_user: Optional[User]) -> PostVO:
        post = self.forum_dao.get_post_by_id(post_id)
        if not post:
            raise PostNotExistsException()

        if record_view:
            self.forum_dao.increment_view_count(post_id)
            if current_user:
                self.forum_dao.record_browse_history(current_user.id, post_id)

        vo = PostVO.model_validate(post)

        if current_user:
            vote = self.forum_dao.get_post_vote(current_user.id, post_id)
            if vote:
                vo.my_vote = vote.vote_type

        return vo

    def get_post_page(self, dto: PostQueryDTO, current_user: Optional[User]) -> PageData[PostVO]:
        total, records = self.forum_dao.get_posts_page(dto)
        vo_list = []
        for p in records:
            post_info = PostVO.model_validate(p)
            # TODO 这里可以替换成大模型总结
            post_info.content = utils.extract_summary(post_info.content, 30)
            vo_list.append(post_info)

        # 如果用户已登录，并且当前页有数据，进行批量状态拼装
        if current_user and vo_list:
            post_ids = [vo.id for vo in vo_list]
            vote_map = self.forum_dao.get_user_post_votes_batch(current_user.id, post_ids)
            for vo in vo_list:
                vo.my_vote = vote_map.get(vo.id, 0)

        return PageData(total=total, page=dto.page, size=dto.size, records=vo_list)


    def get_browse_post_record(self, user_id, page, size):
        total, ids = self.forum_dao.get_post_browse_ids(user_id, page, size)
        vo_list = []
        for post_id in ids:
            post = self.forum_dao.get_post_by_id(post_id)
            if post is None:
                continue
            post_vo = PostVO.model_validate(post)
            post_vo.content = utils.extract_summary(post_vo.content, 30)
            vo_list.append(post_vo)

        post_ids = [vo.id for vo in vo_list]
        vote_map = self.forum_dao.get_user_post_votes_batch(user_id, post_ids)
        for vo in vo_list:
            vo.my_vote = vote_map.get(vo.id, 0)

        return total, vo_list


    def update_post(self, dto: PostUpdateDTO, current_user: User) -> PostVO:
        # 查出帖子
        post = self.forum_dao.get_post_by_id(dto.post_id)
        if not post:
            raise PostNotExistsException()

        # 权限校验：只能是发帖人本人修改
        if post.user_id != current_user.id:
            raise UserNotPermittedException()

        # 传了值才更新
        if dto.title is not None:
            post.title = dto.title
        if dto.content is not None:
            post.content = dto.content
        if dto.cover_image is not None:
            post.cover_image = dto.cover_image

        # 提交保存
        updated_post = self.forum_dao.update_post(post)

        # 返回更新后的VO
        return PostVO.model_validate(updated_post)

    # ---------------- 评论业务 ----------------
    def create_comment(self, dto: CommentCreateDTO, current_user: User) -> CommentVO:
        # 校验帖子是否存在
        post = self.forum_dao.get_post_by_id(dto.post_id)
        if not post:
            raise PostNotExistsException()

        # 控制楼中楼层级：传进来的 parent_id 必须是一级评论！
        if dto.parent_id:
            parent_comment = self.forum_dao.get_comment_by_id(dto.parent_id)
            if not parent_comment:
                raise CommentNotExistsException()

            # 如果回复的目标本身就有 parent_id，说明是个二级评论
            if parent_comment.parent_id is not None:
                raise InvalidCommentLevelException()

        # 构建实体并入库
        new_comment = Comment(
            post_id=dto.post_id,
            user_id=current_user.id,
            content=dto.content,
            parent_id=dto.parent_id,
            reply_to_user_id=dto.reply_to_user_id
        )
        saved_comment = self.forum_dao.create_comment(new_comment)

        # 同步增加帖子的评论总数
        post.comment_count += 1
        self.forum_dao.update_post(post)

        comment_vo = CommentVO.model_validate(saved_comment)

        user_cur_comment = self.user_dao.get_user_by_id(comment_vo.user_id)
        if not user_cur_comment:
            raise UserNotFoundException()
        comment_vo.user_name = user_cur_comment.username
        comment_vo.user_avatar_url = user_cur_comment.avatar
        if comment_vo.reply_to_user_id:
            user_reply = self.user_dao.get_user_by_id(comment_vo.reply_to_user_id)
            comment_vo.reply_to_user_name = user_reply.username

        return comment_vo

    def delete_comment(self, comment_id: int, current_user: User):
        comment = self.forum_dao.get_comment_by_id(comment_id)
        if not comment:
            raise CommentNotExistsException()

        # 权限校验：只能删除自己的，或者管理员删
        if comment.user_id != current_user.id and current_user.role != "admin":
            raise UserNotPermittedException()

        # 逻辑删除
        comment.is_deleted = True
        self.forum_dao.update_comment(comment)

        # 同步扣减帖子的评论数
        post = self.forum_dao.get_post_by_id(comment.post_id)
        if post and post.comment_count > 0:
            post.comment_count -= 1
            self.forum_dao.update_post(post)

        return True

    def get_post_comment_tree(self, post_id: int, current_user: Optional[User]) -> list[RootCommentVO]:
        comments = self.forum_dao.get_comments_by_post(post_id)
        if not comments:
            return []

        # 批量查出当前用户对这些评论的点赞状态
        vote_map = {}
        if current_user:
            comment_ids = [c.id for c in comments]
            vote_map = self.forum_dao.get_user_comment_votes_batch(current_user.id, comment_ids)

        root_comments_map = {}
        children_dict = defaultdict(list)

        for c in comments:
            if c.parent_id is None:
                vo = RootCommentVO.model_validate(c)

                # 加入发帖人部分信息
                user_cur_comment = self.user_dao.get_user_by_id(vo.user_id)
                if not user_cur_comment:
                    raise UserNotFoundException()
                vo.user_name = user_cur_comment.username
                vo.user_avatar_url = user_cur_comment.avatar

                # 注入 my_vote
                vo.my_vote = vote_map.get(c.id, 0)
                root_comments_map[c.id] = vo
            else:
                vo = CommentVO.model_validate(c)

                # 加入发帖人部分信息
                user_cur_comment = self.user_dao.get_user_by_id(vo.user_id)
                if not user_cur_comment:
                    raise UserNotFoundException()
                vo.user_name = user_cur_comment.username
                vo.user_avatar_url = user_cur_comment.avatar

                #加入回复人名称
                if vo.reply_to_user_id:
                    user_reply = self.user_dao.get_user_by_id(vo.reply_to_user_id)
                    vo.reply_to_user_name = user_reply.username

                # 注入 my_vote
                vo.my_vote = vote_map.get(c.id, 0)
                children_dict[c.parent_id].append(vo)

        result_tree = []
        for root_id, root_vo in root_comments_map.items():
            if root_id in children_dict:
                root_vo.children = children_dict[root_id]
            result_tree.append(root_vo)

        return result_tree

    # ---------------- 互动业务 (帖子的赞/踩) ----------------
    def vote_post(self, dto: PostVoteDTO, current_user: User):
        # 检查帖子是否存在
        post = self.forum_dao.get_post_by_id(dto.post_id)
        if not post:
            raise PostNotExistsException()

        # 查询历史评价记录
        existing_vote = self.forum_dao.get_post_vote(current_user.id, dto.post_id)

        if not existing_vote:
            # 场景 A: 之前没表态过，【纯新增】
            new_vote = PostVote(user_id=current_user.id, post_id=dto.post_id, vote_type=dto.vote_type)
            self.forum_dao.db.add(new_vote)
            if dto.vote_type == 1:
                post.upvote_count += 1
            else:
                post.downvote_count += 1
        else:
            # 场景 B: 之前表态过
            if existing_vote.vote_type == dto.vote_type:
                # 场景 B-1: 这次点的跟上次一样 -> 【取消操作】 (删记录，减数量)
                self.forum_dao.db.delete(existing_vote)
                if dto.vote_type == 1:
                    post.upvote_count -= 1
                else:
                    post.downvote_count -= 1
            else:
                # 场景 B-2: 赞变踩，或者踩变赞 -> 【反转操作】 (改记录，双向调数量)
                existing_vote.vote_type = dto.vote_type
                self.forum_dao.db.add(existing_vote)
                if dto.vote_type == 1:
                    post.upvote_count += 1
                    post.downvote_count -= 1
                else:
                    post.upvote_count -= 1
                    post.downvote_count += 1

        # 3. 统一提交事务（保证数据强一致性）
        self.forum_dao.db.add(post)
        self.forum_dao.db.commit()
        return True

    # ---------------- 互动业务 (评论的赞/踩) ----------------
    def vote_comment(self, dto: CommentVoteDTO, current_user: User):
        # 逻辑与帖子完全一致，只是操作的对象变了
        comment = self.forum_dao.get_comment_by_id(dto.comment_id)
        if not comment:
            raise CommentNotExistsException()

        existing_vote = self.forum_dao.get_comment_vote(current_user.id, dto.comment_id)

        if not existing_vote:
            new_vote = CommentVote(user_id=current_user.id, comment_id=dto.comment_id, vote_type=dto.vote_type)
            self.forum_dao.db.add(new_vote)
            if dto.vote_type == 1:
                comment.upvote_count += 1
            else:
                comment.downvote_count += 1
        else:
            if existing_vote.vote_type == dto.vote_type:
                self.forum_dao.db.delete(existing_vote)
                if dto.vote_type == 1:
                    comment.upvote_count -= 1
                else:
                    comment.downvote_count -= 1
            else:
                existing_vote.vote_type = dto.vote_type
                self.forum_dao.db.add(existing_vote)
                if dto.vote_type == 1:
                    comment.upvote_count += 1
                    comment.downvote_count -= 1
                else:
                    comment.upvote_count -= 1
                    comment.downvote_count += 1

        self.forum_dao.db.add(comment)
        self.forum_dao.db.commit()
        return True

    def get_recommended_posts_page(self, book_ids: list[int], page: int, size: int, current_user: Optional[User]) -> \
    PageData[PostVO]:
        """
        获取分页推荐帖子
        """
        # 1. 调用 DAO 层的统一查询
        total, posts = self.forum_dao.get_unified_recommend_posts_page(book_ids, page, size)

        # 2. 实体转换与内容摘要提取
        vo_list = []
        for p in posts:
            post_info = PostVO.model_validate(p)
            post_info.content = utils.extract_summary(post_info.content, 30)
            vo_list.append(post_info)

        # 3. 如果用户已登录，批量拼装点赞/踩状态
        if current_user and vo_list:
            post_ids_list = [vo.id for vo in vo_list]
            vote_map = self.forum_dao.get_user_post_votes_batch(current_user.id, post_ids_list)
            for vo in vo_list:
                vo.my_vote = vote_map.get(vo.id, 0)

        return PageData(total=total, page=page, size=size, records=vo_list)

    def submit_report(self, dto: ReportCreateDTO, user_id: int) -> None:
        """
        [C端] 提交举报
        """
        # 1. 校验 target_type 是否合法
        valid_types = ["board", "post", "comment"]
        if dto.target_type not in valid_types:
            raise IllegalReportTypeException()

        # 2. 校验目标实体是否存在 (复用现有的查询方法)
        target_exists = False
        if dto.target_type == "board":
            board = self.forum_dao.get_board_by_id(dto.target_id)
            target_exists = board is not None and board.is_active
        elif dto.target_type == "post":
            target_exists = self.forum_dao.get_post_by_id(dto.target_id) is not None
        elif dto.target_type == "comment":
            target_exists = self.forum_dao.get_comment_by_id(dto.target_id) is not None

        if not target_exists:
            raise IllegalReportTypeException()

        # 3. 构建实体并保存
        new_report = Report(
            user_id=user_id,
            target_type=dto.target_type,
            target_id=dto.target_id,
            reason=dto.reason
        )
        self.forum_dao.create_report(new_report)

    def get_report_page(self, query_dto: ReportAdminQueryDTO) -> PageData[ReportAggregatedVO]:
        """获取聚合举报列表并拼装预览信息"""
        total, records = self.forum_dao.get_aggregated_reports_page(query_dto)

        vo_list = []
        for record in records:
            # record 为 SQLModel 解析出的 tuple
            t_type, t_id, r_count, latest_time = record

            # 动态抓取被举报对象的内容片段作为预览
            preview_text = "[目标已删除或无法预览]"
            if t_type == "board":
                board = self.forum_dao.get_board_by_id(t_id)
                if board:
                    preview_text = f"板块名称: {board.name}"
            elif t_type == "post":
                post = self.forum_dao.get_post_by_id(t_id)
                if post:
                    preview_text = f"帖子标题: {post.title}"
            elif t_type == "comment":
                comment = self.forum_dao.get_comment_by_id(t_id)
                if comment:
                    preview_text = f"评论内容: {comment.content[:30]}..."  # 截取前30字

            vo_list.append(ReportAggregatedVO(
                target_type=t_type,
                target_id=t_id,
                report_count=r_count,
                latest_report_time=latest_time,
                target_preview_text=preview_text
            ))

        return PageData(total=total, page=query_dto.page, size=query_dto.size, records=vo_list)

    def get_admin_report_detail(self, target_type: str, target_id: int, status: int) -> list[ReportDetailVO]:
        """获取具体的举报工单列表"""
        reports = self.forum_dao.get_report_details(target_type, target_id, status)
        return [ReportDetailVO.model_validate(r) for r in reports]

    def process_reports(self, dto: ReportProcessDTO) -> str:
        """
        [管理端] 处理举报工单：一键封禁内容并结案
        """
        # 1. 如果 action == 1 (判定违规)，则执行内容的逻辑删除/封禁
        if dto.action == 1:
            if dto.target_type == "board":
                target = self.forum_dao.get_board_by_id(dto.target_id)
                if target: target.is_active = False
            elif dto.target_type == "post":
                target = self.forum_dao.get_post_by_id(dto.target_id)
                if target: target.is_deleted = True
            elif dto.target_type == "comment":
                target = self.forum_dao.get_comment_by_id(dto.target_id)
                if target: target.is_deleted = True

            # 保存内容状态修改
            if target:
                self.forum_dao.db.add(target)

        # 无论 action 是 1 还是 2，都批量更新举报单状态
        self.forum_dao.update_reports_status_batch(
            target_type=dto.target_type,
            target_id=dto.target_id,
            new_status=dto.action,
            remark=dto.remark
        )

        # 3. 统一提交事务
        self.forum_dao.db.commit()

        return "内容已下架并处理相关工单" if dto.action == 1 else "已驳回该举报"
