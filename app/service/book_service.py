from typing import Optional
from fastapi import Depends

from app.core.constants import ActionWeight
from app.dao.book_dao import BookDao
from app.exceptions.book_exceptions import BookNotExistsException, BookAlreadyExistsException
from app.exceptions.user_exceptions import UserNotPermittedException
from app.models import BookVote, BookFavorite, Book
from app.models.book import TagIndex
from app.models.user import User
from app.recommend.interest_service import UserInterestService
from app.recommend.matrix_cache import book_matrix_cache
from app.schemas.book_schema import BookQueryDTO, BookVO, BookVoteDTO, BookFavoriteDTO, BookCreateDTO, BookUpdateDTO, \
    BookSuggestVO, BookAdminQueryDTO, BookAdminVO, BookStatusUpdateDTO
from app.schemas.result import PageData
from sklearn.feature_extraction.text import TfidfVectorizer
from app.recommend.vector_utils import VectorConverter
import math

class BookService:
    def __init__(self, dao: BookDao = Depends()):
        self.dao = dao

    def get_book_detail(self, book_id: int, record_view: bool, current_user: Optional[User]) -> BookVO:
        book = self.dao.get_book_by_id(book_id)
        if not book:
            raise BookNotExistsException()

        # 记录浏览行为 浏览量 +1
        if record_view:
            self.dao.increment_view_count(book_id)
            if current_user:
                # 浏览历史记录
                self.dao.record_browse_history(current_user.id, book_id)

                # 推荐系统埋点
                UserInterestService.update_user_interest(
                    self.dao.db,
                    current_user.id,
                    book_id,
                    ActionWeight.VIEW
                )

        vo = BookVO.model_validate(book)

        # 为返回值添加用户的历史行为
        if current_user:
            # 单个状态夹带 (查询点赞)
            vote = self.dao.get_book_vote(current_user.id, book_id)
            if vote:
                vo.my_vote = vote.vote_type

            # 单个状态夹带 (查询收藏/想读状态)
            favorite = self.dao.get_book_favorite(current_user.id, book_id)
            if favorite:
                vo.my_favorite_status = favorite.status

        return vo

    def get_book_detail_for_admin(self, book_id):
        book = self.dao.get_book_by_id_for_admin(book_id)
        if not book:
            raise BookNotExistsException()
        vo = BookVO.model_validate(book)
        return vo

    def get_book_detail_safe(self, book_id: int, record_view: bool, current_user: Optional[User]) -> BookVO | None:
        """
        [内部安全方法] 专用于其他模块的列表数据组装
        """
        book = self.dao.get_book_by_id(book_id)
        if not book:
            return None

        vo = BookVO.model_validate(book)

        # 为返回值添加用户的历史行为 (如果传入了用户)
        if current_user:
            # 查询点赞状态
            vote = self.dao.get_book_vote(current_user.id, book_id)
            if vote:
                vo.my_vote = vote.vote_type

            # 查询收藏/想读状态
            favorite = self.dao.get_book_favorite(current_user.id, book_id)
            if favorite:
                vo.my_favorite_status = favorite.status

        return vo

    def get_book_page(self, dto: BookQueryDTO, current_user: Optional[User]) -> PageData[BookVO]:
        total, records = self.dao.get_books_page(dto)
        vo_list = [BookVO.model_validate(b) for b in records]

        # 批量状态夹带 (针对已登录用户且当前页有数据的情况)
        if current_user and vo_list:
            book_ids = [vo.id for vo in vo_list]

            # 查询当前用户的点赞和收藏记录
            vote_map = self.dao.get_user_book_votes_batch(current_user.id, book_ids)
            favorite_map = self.dao.get_user_book_favorites_batch(current_user.id, book_ids)

            # 遍历拼装到 vo_list 中
            for vo in vo_list:
                vo.my_vote = vote_map.get(vo.id, 0)
                vo.my_favorite_status = favorite_map.get(vo.id, 0)

        return PageData(
            total=total,
            page=dto.page,
            size=dto.size,
            records=vo_list
        )

    def get_book_suggest(self, key_word: str, limit: int) -> list[BookSuggestVO]:
        books = self.dao.get_book_suggests(key_word, limit)
        vo_list = [BookSuggestVO.model_validate(b) for b in books]
        return vo_list

    def get_hot_tags(self):
        # TODO 这里写死了。。。我们后面再说
        return [
            "小说", "文学", "科幻", "历史", "言情",
            "推理", "悬疑", "心理学", "计算机", "科普",
            "传记", "武侠", "漫画"
        ]

    def vote_book(self, dto: BookVoteDTO, current_user: User):
        # 检查书籍是否存在
        book = self.dao.get_book_by_id(dto.book_id)
        if not book:
            raise BookNotExistsException()

        # 查询历史记录
        existing_vote = self.dao.get_book_vote(current_user.id, dto.book_id)

        if not existing_vote:
            # 场景 A: 纯新增
            new_vote = BookVote(user_id=current_user.id, book_id=dto.book_id, vote_type=dto.vote_type)
            self.dao.db.add(new_vote)
            if dto.vote_type == 1:
                book.upvote_count += 1
            else:
                book.downvote_count += 1

            # 用户首次点赞/点踩将会记录爱好 推荐系统埋点
            UserInterestService.update_user_interest(
                self.dao.db,
                current_user.id,
                book.id,
                ActionWeight.UPVOTE * dto.vote_type
            )

        else:
            # 场景 B: 修改或取消
            if existing_vote.vote_type == dto.vote_type:
                # 场景 B-1: 再次点击同样的按钮 -> 取消操作
                self.dao.db.delete(existing_vote)
                if dto.vote_type == 1:
                    book.upvote_count -= 1
                else:
                    book.downvote_count -= 1
            else:
                # 场景 B-2: 赞变踩 / 踩变赞 -> 反转操作
                existing_vote.vote_type = dto.vote_type
                self.dao.db.add(existing_vote)
                if dto.vote_type == 1:
                    book.upvote_count += 1
                    book.downvote_count -= 1
                else:
                    book.upvote_count -= 1
                    book.downvote_count += 1

        # 统一提交事务
        self.dao.db.add(book)
        self.dao.db.commit()
        return True

    # 更新书籍收藏状态
    def favorite_book(self, dto: BookFavoriteDTO, current_user: User):
        book = self.dao.get_book_by_id(dto.book_id)
        if not book:
            raise BookNotExistsException()

        existing_fav = self.dao.get_book_favorite(current_user.id, dto.book_id)

        if not existing_fav:
            # 如果原本就没收藏，前端还传0，直接放行
            if dto.status == 0:
                return True

            # 场景 A: 从未收藏过, 新增，且总收藏数 +1
            new_fav = BookFavorite(user_id=current_user.id, book_id=dto.book_id, status=dto.status)
            self.dao.db.add(new_fav)
            book.favorite_count += 1

            # 用户首次收藏 推荐系统埋点
            UserInterestService.update_user_interest(
                self.dao.db,
                current_user.id,
                book.id,
                ActionWeight.COLLECT
            )
        else:
            # 场景 B: 已经收藏过了
            if dto.status == 0 or existing_fav.status == dto.status:
                # 场景 B-1: 传了 0 (显式取消)，或者传了相同的状态过来 (Toggle取消) -> 删除记录，总数 -1
                self.dao.db.delete(existing_fav)
                book.favorite_count -= 1
            else:
                # 场景 B-2: 状态改变 (比如从"想读"变成了"读过") -> 更新状态，总数不变！
                existing_fav.status = dto.status
                self.dao.db.add(existing_fav)

        self.dao.db.add(book)
        self.dao.db.commit()
        return True

    def create_book(self, dto: BookCreateDTO, current_user: User) -> BookVO:
        # 权限校验
        if current_user.role != "admin":
            raise UserNotPermittedException()

        # 防止重复录入
        existing = self.dao.get_book_by_douban_id(dto.douban_id)
        if existing:
            raise BookAlreadyExistsException()

        # 入库
        new_book = Book(**dto.model_dump())
        saved_book = self.dao.create_book(new_book)

        return BookVO.model_validate(saved_book)

    def update_book(self, dto: BookUpdateDTO, current_user: User) -> BookVO:
        # 权限校验
        if current_user.role != "admin":
            raise UserNotPermittedException()

        # 书籍是否存在
        book = self.dao.get_book_by_id(dto.book_id)
        if not book:
            raise BookNotExistsException()

        # 更新
        update_data = dto.model_dump(exclude_unset=True, exclude={"book_id"})
        for key, value in update_data.items():
            setattr(book, key, value)

        updated_book = self.dao.update_book(book)

        return BookVO.model_validate(updated_book)

    def delete_book(self, book_id: int, current_user: User):
        # 权限校验
        if current_user.role != "admin":
            raise UserNotPermittedException()

        # 书籍是否存在
        book = self.dao.get_book_by_id(book_id)
        if not book:
            raise BookNotExistsException()

        # 下架
        book.is_active = False

        # 更新状态
        self.dao.update_book(book)

        return True

    def refresh_tag_indices(self) -> dict:
        """
        全量扫描书库标签并更新索引表 (增量更新)
        返回新增标签的数量和总标签数
        """
        # 从书籍表中提取所有去重后的标签
        raw_tags_list = self.dao.get_all_book_tags()
        all_unique_tags = set()
        for tags_str in raw_tags_list:
            # 按逗号拆分并去掉空格
            split_tags = [t.strip().lower() for t in tags_str.split(',') if t.strip()]
            all_unique_tags.update(split_tags)

        # 获取数据库中已有的标签映射
        existing_tag_map = self.dao.get_all_tag_indices()

        # 找出库里没有的新标签
        new_tag_names = all_unique_tags - set(existing_tag_map.keys())

        if not new_tag_names:
            return {"new_added": 0, "total_count": len(existing_tag_map)}

        # 计算起始索引并批量构建新实体
        current_max_index = self.dao.get_max_tag_index()
        new_tag_objects = []
        for i, tag_name in enumerate(sorted(list(new_tag_names))):
            new_tag_objects.append(TagIndex(
                tag_name=tag_name,
                index_value=current_max_index + 1 + i
            ))

        # 批量插入
        self.dao.batch_create_tags(new_tag_objects)

        return {
            "new_added": len(new_tag_names),
            "total_count": current_max_index + 1 + len(new_tag_names)
        }

    def calculate_all_books_tfidf(self) -> int:
        """
        计算全库书籍的 TF-IDF 特征向量，并存入数据库
        """
        # 取出所有需要的原料
        books = self.dao.get_all_books_with_tags()
        tag_map = self.dao.get_all_tag_indices()

        if not books or not tag_map:
            return 0

        # 自定义分词器,按逗号切分,并全转小写
        def tag_tokenizer(text):
            return [t.strip().lower() for t in text.split(',') if t.strip()]

        # 实例化 TF-IDF 转换器
        # vocabulary=tag_map 意味着：它算出来的矩阵的列索引，将绝对完美地对应你数据库的 index_value
        vectorizer = TfidfVectorizer(
            tokenizer=tag_tokenizer,
            lowercase=False,  # 因为我们在 tokenizer 里已经 lower() 了
            token_pattern=None,
            vocabulary=tag_map
        )

        # 提取所有书的标签组装成“语料库”列表
        corpus = [book.tags for book in books]

        # 计算得到一个稀疏矩阵 (SciPy CSR Matrix)
        tfidf_matrix = vectorizer.fit_transform(corpus)

        # 将矩阵按行拆解，转成 "1:0.32, 5:0.89" 存回书籍实体
        for i, book in enumerate(books):
            row = tfidf_matrix.getrow(i)  # 取出第 i 本书的向量

            # row.indices 是非零特征的索引数组，row.data 是对应的 TF-IDF 权重数组
            vector_dict = {
                int(idx): float(val)
                for idx, val in zip(row.indices, row.data)
            }

            # 变成字符串塞回给书
            book.tfidf_vector = VectorConverter.dict_to_str(vector_dict)

        # 批量更新所有书籍的 tfidf_vector 字段
        self.dao.commit_changes()

        return len(books)

    def get_personalized_recommendations(self, current_user: User, limit: int = 10) -> list[BookVO]:
        """
        获取个性化书籍推荐
        """
        # 这种情况较为少见，用户首次登录系统的时候将会被迫选择一些tag或者书籍,但是保留应对措施
        if not current_user or not current_user.feature_vector:
            hot_books = self.dao.get_hot_books(limit)
            return [BookVO.model_validate(b) for b in hot_books]

        # 解析用户向量并进行对数平滑
        # user_vector_dict 格式: {tag_index: raw_score}
        user_vector_dict = VectorConverter.str_to_dict(current_user.feature_vector)
        if not user_vector_dict:
            hot_books = self.dao.get_hot_books(limit)
            return [BookVO.model_validate(b) for b in hot_books]

        # normalized_user 格式: {tag_index: ln(1 + raw_score)}
        # 进行对数标准化
        normalized_user = VectorConverter.log_normalize(user_vector_dict)

        # 矩阵相乘 (稀疏向量点乘)
        book_scores = []
        all_book_vectors = book_matrix_cache.get_all_vectors()

        for book_id, book_vector in all_book_vectors.items():
            score = 0.0
            # 如果这本书也有这个标签，就把它们的权重相乘并累加
            for tag_index, user_val in normalized_user.items():
                if tag_index in book_vector:
                    score += user_val * book_vector[tag_index]

            if score > 0:
                book_scores.append((book_id, score))

        # 排序并截取 Top N
        if not book_scores:
            hot_books = self.dao.get_hot_books(limit)
            return [BookVO.model_validate(b) for b in hot_books]

        # 按得分从高到低排序
        book_scores.sort(key=lambda x: x[1], reverse=True)

        # self.debug_print_true_cosine(normalized_user, book_scores)

        top_book_ids = [book_id for book_id, score in book_scores[:limit]]

        # 从数据库获取实体数据
        books = self.dao.get_books_by_ids(top_book_ids)

        #数据库的 IN 查询返回结果通常是无序的，须按得分顺序重新排队
        book_map = {book.id: book for book in books}
        sorted_books = [book_map[bid] for bid in top_book_ids if bid in book_map]

        return [BookVO.model_validate(b) for b in sorted_books]

    def get_similar_books(self, book_id: int, limit: int = 10) -> list[BookVO]:
        """
        根据指定图书获取相似图书推荐 (Item-to-Item)
        """
        # 获取目标书籍的特征向量
        target_vector = book_matrix_cache.get_vector(book_id)

        # 如果目标书籍没有向量，兜底返回热门书籍
        if not target_vector:
            hot_books = self.dao.get_hot_books(limit)
            return [BookVO.model_validate(b) for b in hot_books]

        book_scores = []
        all_book_vectors = book_matrix_cache.get_all_vectors()

        # 遍历全库计算相似度（点乘）
        for current_book_id, current_vector in all_book_vectors.items():
            # 剔除目标书籍本身，不能把这本书自己推荐给自己
            if current_book_id == book_id:
                continue

            score = 0.0
            # 稀疏向量求点乘
            for tag_index, weight in target_vector.items():
                if tag_index in current_vector:
                    score += weight * current_vector[tag_index]

            if score > 0:
                book_scores.append((current_book_id, score))

        # 排序并截取 Top N
        if not book_scores:
            hot_books = self.dao.get_hot_books(limit)
            return [BookVO.model_validate(b) for b in hot_books]

        # 按得分从高到低排序
        book_scores.sort(key=lambda x: x[1], reverse=True)
        top_book_ids = [bid for bid, score in book_scores[:limit]]

        # 从数据库获取实体数据
        books = self.dao.get_books_by_ids(top_book_ids)

        # 数据库的 IN 查询返回结果通常是无序的，须按得分顺序重新排队
        book_map = {book.id: book for book in books}
        sorted_books = [book_map[bid] for bid in top_book_ids if bid in book_map]

        return [BookVO.model_validate(b) for b in sorted_books]

    def get_favorite_books(self, user_id, page, size, status):
        return self.dao.get_favorite_books_page_by_id(user_id, page, size, status)

    def debug_print_true_cosine(self, normalized_user: dict, book_scores_list: list):
        """
        基于已归一化的书籍向量，还原并打印真实的余弦相似度
        normalized_user: {tag_index: user_weight}
        book_scores_list: list of tuples, e.g., [(book_id, raw_dot_product_score), ...]
        """
        if not book_scores_list or not normalized_user:
            return

        # 1. 计算用户向量的 L2 范数 (||U||)
        user_norm = math.sqrt(sum(val ** 2 for val in normalized_user.values()))

        if user_norm == 0:
            print("[-] 用户向量全为0，无法计算标准余弦。")
            return

        print("\n" + "=" * 60)
        print(f"📊 论文数据采集: Top 50 真实余弦相似度 (Cosine Sim)")
        print(f"📌 用户向量长度 (||U||): {user_norm:.4f}")
        print("=" * 60)
        print(f"{'Rank':<6} | {'Book ID':<10} | {'Cosine Sim [0,1]':<18} | {'Raw Dot Product':<15}")
        print("-" * 60)

        # 截取前 50 名
        top_50 = book_scores_list[:50]

        for rank, (b_id, raw_dot_score) in enumerate(top_50, 1):
            # 2. 还原真实余弦值：点积 / (||U|| * 1)
            true_cosine = raw_dot_score / user_norm
            print(f"{rank:<6} | {b_id:<10} | {true_cosine:<18.6f} | {raw_dot_score:<15.6f}")

        print("=" * 60 + "\n")

    def get_admin_book_page(self, query_dto: BookAdminQueryDTO) -> PageData[BookAdminVO]:
        """
        [管理端] 获取图书分页列表
        """
        # 调 DAO 查数据
        total, records = self.dao.get_books_page_for_admin(query_dto)
        vo_list = [BookAdminVO.model_validate(book) for book in records]

        # 组装
        return PageData(
            total=total,
            page=query_dto.page,
            size=query_dto.size,
            records=vo_list
        )

    def update_book_status_for_admin(self, book_id: int, update_dto: BookStatusUpdateDTO) -> None:
        """
        [管理端] 调整图书上下架状态
        """
        # 查出目标图书
        target_book = self.dao.get_book_by_id_for_admin(book_id)
        if not target_book:
            raise BookNotExistsException()

        # 更新状态并保存
        target_book.is_active = update_dto.is_active
        self.dao.update_book(target_book)

        # 通知缓存
        if update_dto.is_active:
            # 上架
            vector_dict = VectorConverter.str_to_dict(target_book.tfidf_vector)
            book_matrix_cache.update_vector(book_id, vector_dict)
        else:
            book_matrix_cache.remove_vector(book_id)
