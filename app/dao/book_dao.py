from pymysql import IntegrityError
from sqlmodel import Session, select, func, or_, col
from fastapi import Depends
from app.core.db import get_db
from app.models.book import Book, BookBrowseHistory, BookVote, BookFavorite, TagIndex  # 假设你的实体在这个路径
from app.schemas.book_schema import BookQueryDTO, BookAdminQueryDTO


class BookDao:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    # 根据id获得书
    def get_book_by_id(self, book_id: int) -> Book | None:
        statement = select(Book).where(Book.id == book_id, Book.is_active == True)
        return self.db.exec(statement).first()

    # 增加一本书的阅读量
    def increment_view_count(self, book_id: int):
        book = self.get_book_by_id(book_id)
        if book:
            book.view_count += 1
            self.db.add(book)
            self.db.commit()

    # 分页查询书籍
    def get_books_page(self, dto: "BookQueryDTO") -> tuple[int, list[Book]]:
        statement = select(Book).where(Book.is_active == True)

        # 动态条件拼接
        if dto.keyword:
            # 模糊匹配书名、作者或 ISBN
            search_str = f"%{dto.keyword}%"
            statement = statement.where(
                or_(
                    Book.title.like(search_str),
                    Book.author.like(search_str),
                    Book.isbn.like(search_str)
                )
            )

        if dto.tag:
            # 标签模糊匹配 (因为数据库存的是逗号分隔的字符串)
            statement = statement.where(Book.tags.like(f"%{dto.tag}%"))

        # 2. 统计总数
        count_statement = select(func.count()).select_from(statement.subquery())
        total = self.db.exec(count_statement).one()

        # 3. 动态排序
        if dto.sort_by == "hot":
            statement = statement.order_by(Book.view_count.desc(), Book.id.desc())
        elif dto.sort_by == "rating":
            statement = statement.order_by(Book.douban_rating.desc(), Book.id.desc())
        else:
            # 默认按创建时间倒序
            statement = statement.order_by(Book.create_time.desc())

        # 4. 分页提取
        statement = statement.offset((dto.page - 1) * dto.size).limit(dto.size)
        records = self.db.exec(statement).all()

        return total, records

    def get_book_suggests(self, key_word: str, limit: int) -> list[Book | None]:
        search_str = f"%{key_word}%"
        statement = select(Book).where(Book.is_active == True)
        statement = statement.where(
            or_(
                Book.title.like(search_str),
                Book.author.like(search_str),
                Book.isbn.like(search_str)
            )
        )
        statement = statement.order_by(Book.view_count.desc(), Book.id.desc())
        statement = statement.limit(limit)
        books = self.db.exec(statement).all()
        return books


    def record_browse_history(self, user_id: int, book_id: int):
        """记录浏览历史：存在则更新次数和时间，不存在则新增"""
        statement = select(BookBrowseHistory).where(
            BookBrowseHistory.user_id == user_id,
            BookBrowseHistory.book_id == book_id
        )
        history = self.db.exec(statement).first()

        if history:
            history.view_times += 1
            self.db.add(history)
        else:
            new_history = BookBrowseHistory(user_id=user_id, book_id=book_id)
            self.db.add(new_history)

        self.db.commit()

    def get_book_vote(self, user_id: int, book_id: int) -> BookVote | None:
        statement = select(BookVote).where(BookVote.user_id == user_id, BookVote.book_id == book_id)
        return self.db.exec(statement).first()

    def get_book_favorite(self, user_id: int, book_id: int) -> BookFavorite | None:
        statement = select(BookFavorite).where(BookFavorite.user_id == user_id, BookFavorite.book_id == book_id)
        return self.db.exec(statement).first()

    # ---------------- 批量状态查询 (用于分页列表) ----------------
    def get_user_book_votes_batch(self, user_id: int, book_ids: list[int]) -> dict[int, int]:
        if not book_ids:
            return {}
        statement = select(BookVote).where(
            BookVote.user_id == user_id,
            BookVote.book_id.in_(book_ids)
        )
        votes = self.db.exec(statement).all()
        return {v.book_id: v.vote_type for v in votes}

    def get_user_book_favorites_batch(self, user_id: int, book_ids: list[int]) -> dict[int, int]:
        if not book_ids:
            return {}
        statement = select(BookFavorite).where(
            BookFavorite.user_id == user_id,
            BookFavorite.book_id.in_(book_ids)
        )
        favorites = self.db.exec(statement).all()
        return {f.book_id: f.status for f in favorites}

    def get_favorite_books_page_by_id(self, user_id, page, size, status):
        """获取用户的图书收藏分页并且过滤下架书籍"""
        # 连表 Book
        statement = (
            select(BookFavorite.book_id)
            .join(Book, BookFavorite.book_id == Book.id)
            .where(
                BookFavorite.user_id == user_id,
                Book.is_active == True  # 核心防御：只查活着的书
            )
        )

        # 状态过滤
        if status != 0:
            statement = statement.where(BookFavorite.status == status)

        # 排序
        statement = statement.order_by(BookFavorite.create_time.desc())

        # total
        count_statement = select(func.count()).select_from(statement.subquery())
        total = self.db.exec(count_statement).one()

        # 分页
        statement = statement.offset((page - 1) * size).limit(size)
        ids = self.db.exec(statement).all()

        return total, ids

    def get_book_by_douban_id(self, douban_id: str) -> Book | None:
        """根据豆瓣ID查询书籍 (包含已下架的，防止重复录入)"""
        statement = select(Book).where(Book.douban_id == douban_id)
        return self.db.exec(statement).first()

    def create_book(self, book: Book) -> Book:
        """纯粹的入库操作"""
        self.db.add(book)
        self.db.commit()
        self.db.refresh(book)
        return book

    def update_book(self, book: Book) -> Book:
        """纯粹的更新操作 (也用于逻辑删除)"""
        self.db.add(book)
        self.db.commit()
        self.db.refresh(book)
        return book

    def get_all_book_tags(self) -> list[str]:
        """获取库中所有书籍的原始标签字符串列表"""
        statement = select(Book.tags).where(Book.tags is not None)
        return self.db.exec(statement).all()

    def get_all_tag_indices(self) -> dict[str, int]:
        """获取当前已存在的所有标签映射 Map"""
        statement = select(TagIndex)
        results = self.db.exec(statement).all()
        return {item.tag_name: item.index_value for item in results}

    def get_max_tag_index(self) -> int:
        """获取当前最大的索引值"""
        statement = select(func.max(TagIndex.index_value))
        result = self.db.exec(statement).first()
        return result if result is not None else -1

    def batch_create_tags(self, tag_objects: list[TagIndex]):
        """批量插入"""
        if tag_objects:
            self.db.add_all(tag_objects)
            self.db.commit()

    def get_all_books_with_tags(self) -> list[Book]:
        """获取所有带有标签的书籍"""
        statement = select(Book).where(Book.tags is not None, Book.is_active == True)
        return self.db.exec(statement).all()

    def commit_changes(self):
        """统一提交当前 Session 中的所有变更"""
        self.db.commit()

    def get_books_by_ids(self, book_ids: list[int]) -> list[Book]:
        """根据 ID 列表批量查询书籍"""
        if not book_ids:
            return []
        statement = select(Book).where(col(Book.id).in_(book_ids), Book.is_active == True)
        return self.db.exec(statement).all()

    def get_hot_books(self, limit: int = 10) -> list[Book]:
        """获取全站热门书籍 (按浏览量或收藏量降序，用于冷启动)"""
        statement = select(Book).where(Book.is_active == True).order_by(Book.view_count.desc()).limit(limit)
        return self.db.exec(statement).all()

    def get_tag_names_by_indices(self, indices: list[int]) -> list[str]:
        """根据索引值列表反向解析出标签中文名称"""
        if not indices:
            return []
        # col() 是 sqlmodel 处理 in_ 的标准写法
        statement = select(TagIndex.tag_name).where(col(TagIndex.index_value).in_(indices))
        return self.db.exec(statement).all()

    def get_books_page_for_admin(self, dto: BookAdminQueryDTO) -> tuple[int, list[Book]]:
        """
        [管理端] 分页条件查询图书列表 (包含已下架的图书)
        """
        statement = select(Book)

        # 1. 动态拼接条件
        if dto.keyword:
            search_str = f"%{dto.keyword}%"
            statement = statement.where(
                or_(
                    Book.title.like(search_str),
                    Book.author.like(search_str),
                    Book.isbn.like(search_str)
                )
            )

        # 核心逻辑：根据传入状态过滤，如果不传则查全部
        if dto.is_active is not None:
            statement = statement.where(Book.is_active == dto.is_active)

        # 2. 统计符合条件的总数
        count_statement = select(func.count()).select_from(statement.subquery())
        total = self.db.exec(count_statement).one()

        sort_mapping = {
            "id": Book.id,
            "douban_id": Book.douban_id,
            "title": Book.title,
            "author": Book.author,
            "isbn": Book.isbn,
            "view_count": Book.view_count,
            "create_time": Book.create_time,
        }

        # 获取目标排序字段，如果前端传了不认识的字段，则回退到 create_time
        sort_column = sort_mapping.get(dto.sort_by, Book.create_time)

        # 根据方向应用排序
        if dto.sort_order.lower() == "asc":
            statement = statement.order_by(sort_column.asc())
        else:
            statement = statement.order_by(sort_column.desc())

        # 4. 分页提取
        statement = statement.offset((dto.page - 1) * dto.size).limit(dto.size)
        records = self.db.exec(statement).all()

        return total, records

    def get_book_by_id_for_admin(self, book_id: int) -> Book | None:
        """
        [管理端] 根据ID获取图书详情 (无视上下架状态，专供管理端使用)
        """
        statement = select(Book).where(Book.id == book_id)
        return self.db.exec(statement).first()

    def get_total_books(self) -> int:
        """获取总图书数"""
        statement = select(func.count(Book.id))
        return self.db.exec(statement).one()