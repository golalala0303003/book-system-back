from sqlmodel import Session, select
from app.models.book import Book
from app.recommend.vector_utils import VectorConverter


class BookMatrixCache:
    _instance = None

    # 保险，但是还是不要直接实例化，请直接import book_matrix_cache
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(BookMatrixCache, cls).__new__(cls)
            # 存储结构: {book_id: {tag_index: tfidf_weight}}
            cls._instance._vectors = {}
        return cls._instance

    def reload(self, db: Session) -> int:
        """
        从数据库全量加载 TF-IDF 向量至内存。
        启动时调用
        """
        statement = select(Book.id, Book.tfidf_vector).where(Book.tfidf_vector is not None)
        results = db.exec(statement).all()

        new_cache = {}
        for book_id, vector_str in results:
            if vector_str:
                new_cache[book_id] = VectorConverter.str_to_dict(vector_str)

        # 原子替换，避免在并发请求时读到空数据
        self._vectors = new_cache
        return len(self._vectors)

    def get_all_vectors(self) -> dict[int, dict[int, float]]:
        """获取全量数据字典"""
        return self._vectors

    def get_vector(self, book_id: int) -> dict[int, float]:
        """获取单本书的向量字典"""
        return self._vectors.get(book_id, {})


# 暴露全局唯一实例
book_matrix_cache = BookMatrixCache()