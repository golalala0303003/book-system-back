from fastapi import Depends
from app.dao.forum_dao import ForumDao
from app.exceptions.user_exceptions import UserNotPermittedException
from app.models.user import User
from app.models.forum import Board, Post, Comment, CommentVote, PostVote
from app.schemas.forum_schema import BoardCreateDTO, BoardVO, PostCreateDTO, PostVO, PostQueryDTO, PostUpdateDTO, \
    CommentCreateDTO, CommentVO, RootCommentVO, CommentVoteDTO, PostVoteDTO
from app.exceptions.forum_exceptions import BoardAlreadyExistsException, BoardNotExistsException, \
    PostNotExistsException, CommentNotExistsException, InvalidCommentLevelException
from app.schemas.result import PageData
from collections import defaultdict
from typing import Optional


class ForumService:
    def __init__(self, dao: ForumDao = Depends()):
        self.dao = dao

    # ---------------- 板块业务 ----------------
    def create_board(self, dto: BoardCreateDTO, current_user: User) -> BoardVO:
        # 校验板块名是否重复
        existing_board = self.dao.get_board_by_name(dto.name)
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
        saved_board = self.dao.create_board(new_board)

        # 返回 VO
        return BoardVO.model_validate(saved_board)

    def delete_board(self, board_id: int, current_user: User):
        # 权限校验:只允许管理员删除
        if current_user.role != "admin":
            raise UserNotPermittedException()

        # 检查板块是否存在
        board = self.dao.get_board_by_id(board_id)
        if not board:
            raise BoardNotExistsException()

        # 逻辑删除（隐藏）
        board.is_active = False
        self.dao.update_board(board)
        return True

    def get_all_boards(self) -> list[BoardVO]:
        boards = self.dao.get_active_boards()
        return [BoardVO.model_validate(b) for b in boards]

    # ---------------- 帖子业务 ----------------
    def create_post(self, dto: PostCreateDTO, current_user: User) -> PostVO:
        # 校验板块是否存在且处于激活状态
        board = self.dao.get_board_by_id(dto.board_id)
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
        saved_post = self.dao.create_post(new_post)
        return PostVO.model_validate(saved_post)

    def delete_post(self, post_id: int, current_user: User):
        # 查出帖子
        post = self.dao.get_post_by_id(post_id)
        if not post:
            raise PostNotExistsException()

        # 权限校验：发帖人本人 或者 管理员可以删除
        if post.user_id != current_user.id and current_user.role != "admin":
            raise UserNotPermittedException()

        # 逻辑删除
        post.is_deleted = True
        self.dao.update_post(post)

        # TODO 删除关联的评论
        return True

    def get_post_detail(self, post_id: int, current_user: Optional[User]) -> PostVO:
        post = self.dao.get_post_by_id(post_id)
        if not post:
            raise PostNotExistsException()

        self.dao.increment_view_count(post_id)

        vo = PostVO.model_validate(post)

        if current_user:
            vote = self.dao.get_post_vote(current_user.id, post_id)
            if vote:
                vo.my_vote = vote.vote_type

        return vo

    def get_post_page(self, dto: PostQueryDTO, current_user: Optional[User]) -> PageData[PostVO]:
        total, records = self.dao.get_posts_page(dto)
        vo_list = [PostVO.model_validate(p) for p in records]

        # 如果用户已登录，并且当前页有数据，进行批量状态拼装
        if current_user and vo_list:
            post_ids = [vo.id for vo in vo_list]
            vote_map = self.dao.get_user_post_votes_batch(current_user.id, post_ids)
            for vo in vo_list:
                vo.my_vote = vote_map.get(vo.id, 0)

        return PageData(total=total, page=dto.page, size=dto.size, records=vo_list)

    def record_user_view_history(self, cur_user_id, post_id):
        # TODO 完善浏览记录逻辑
        print(f"该用户{cur_user_id}阅读了{post_id}帖子")

    def update_post(self, dto: PostUpdateDTO, current_user: User) -> PostVO:
        # 查出帖子
        post = self.dao.get_post_by_id(dto.post_id)
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
        updated_post = self.dao.update_post(post)

        # 返回更新后的VO
        return PostVO.model_validate(updated_post)

    # ---------------- 评论业务 ----------------
    def create_comment(self, dto: CommentCreateDTO, current_user: User) -> CommentVO:
        # 校验帖子是否存在
        post = self.dao.get_post_by_id(dto.post_id)
        if not post:
            raise PostNotExistsException()

        # 控制楼中楼层级：传进来的 parent_id 必须是一级评论！
        if dto.parent_id:
            parent_comment = self.dao.get_comment_by_id(dto.parent_id)
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
        saved_comment = self.dao.create_comment(new_comment)

        # 同步增加帖子的评论总数
        post.comment_count += 1
        self.dao.update_post(post)

        return CommentVO.model_validate(saved_comment)

    def delete_comment(self, comment_id: int, current_user: User):
        comment = self.dao.get_comment_by_id(comment_id)
        if not comment:
            raise CommentNotExistsException()

        # 权限校验：只能删除自己的，或者管理员删
        if comment.user_id != current_user.id and current_user.role != "admin":
            raise UserNotPermittedException()

        # 逻辑删除
        comment.is_deleted = True
        self.dao.update_comment(comment)

        # 同步扣减帖子的评论数
        post = self.dao.get_post_by_id(comment.post_id)
        if post and post.comment_count > 0:
            post.comment_count -= 1
            self.dao.update_post(post)

        return True

    def get_post_comment_tree(self, post_id: int, current_user: Optional[User]) -> list[RootCommentVO]:
        comments = self.dao.get_comments_by_post(post_id)
        if not comments:
            return []

        # 批量查出当前用户对这些评论的点赞状态
        vote_map = {}
        if current_user:
            comment_ids = [c.id for c in comments]
            vote_map = self.dao.get_user_comment_votes_batch(current_user.id, comment_ids)

        root_comments_map = {}
        children_dict = defaultdict(list)

        for c in comments:
            if c.parent_id is None:
                vo = RootCommentVO.model_validate(c)
                # 注入 my_vote
                vo.my_vote = vote_map.get(c.id, 0)
                root_comments_map[c.id] = vo
            else:
                vo = CommentVO.model_validate(c)
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
        post = self.dao.get_post_by_id(dto.post_id)
        if not post:
            raise PostNotExistsException()

        # 查询历史评价记录
        existing_vote = self.dao.get_post_vote(current_user.id, dto.post_id)

        if not existing_vote:
            # 场景 A: 之前没表态过，【纯新增】
            new_vote = PostVote(user_id=current_user.id, post_id=dto.post_id, vote_type=dto.vote_type)
            self.dao.db.add(new_vote)
            if dto.vote_type == 1:
                post.upvote_count += 1
            else:
                post.downvote_count += 1
        else:
            # 场景 B: 之前表态过
            if existing_vote.vote_type == dto.vote_type:
                # 场景 B-1: 这次点的跟上次一样 -> 【取消操作】 (删记录，减数量)
                self.dao.db.delete(existing_vote)
                if dto.vote_type == 1:
                    post.upvote_count -= 1
                else:
                    post.downvote_count -= 1
            else:
                # 场景 B-2: 赞变踩，或者踩变赞 -> 【反转操作】 (改记录，双向调数量)
                existing_vote.vote_type = dto.vote_type
                self.dao.db.add(existing_vote)
                if dto.vote_type == 1:
                    post.upvote_count += 1
                    post.downvote_count -= 1
                else:
                    post.upvote_count -= 1
                    post.downvote_count += 1

        # 3. 统一提交事务（保证数据强一致性）
        self.dao.db.add(post)
        self.dao.db.commit()
        return True

    # ---------------- 互动业务 (评论的赞/踩) ----------------
    def vote_comment(self, dto: CommentVoteDTO, current_user: User):
        # 逻辑与帖子完全一致，只是操作的对象变了
        comment = self.dao.get_comment_by_id(dto.comment_id)
        if not comment:
            raise CommentNotExistsException()

        existing_vote = self.dao.get_comment_vote(current_user.id, dto.comment_id)

        if not existing_vote:
            new_vote = CommentVote(user_id=current_user.id, comment_id=dto.comment_id, vote_type=dto.vote_type)
            self.dao.db.add(new_vote)
            if dto.vote_type == 1:
                comment.upvote_count += 1
            else:
                comment.downvote_count += 1
        else:
            if existing_vote.vote_type == dto.vote_type:
                self.dao.db.delete(existing_vote)
                if dto.vote_type == 1:
                    comment.upvote_count -= 1
                else:
                    comment.downvote_count -= 1
            else:
                existing_vote.vote_type = dto.vote_type
                self.dao.db.add(existing_vote)
                if dto.vote_type == 1:
                    comment.upvote_count += 1
                    comment.downvote_count -= 1
                else:
                    comment.upvote_count -= 1
                    comment.downvote_count += 1

        self.dao.db.add(comment)
        self.dao.db.commit()
        return True