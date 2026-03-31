from sqlmodel import Session, select
from app.models.user import User
from app.recommend.vector_utils import VectorConverter
from app.recommend.matrix_cache import book_matrix_cache



class UserInterestService:
    @staticmethod
    def update_user_interest(db: Session, user_id: int, book_id: int, weight: float):
        """
        核心接口：根据用户行为更新偏好向量
        :param db: 数据库会话
        :param user_id: 用户ID
        :param book_id: 发生行为的书籍ID
        :param weight: 行为权重 (来自 ActionWeight)
        """
        # 获取书籍的 TF-IDF 向量
        book_vector = book_matrix_cache.get_vector(book_id)
        if not book_vector:
            return

        # 获取用户当前的特征向量
        user = db.get(User, user_id)
        if not user:
            return

        user_vector_dict = VectorConverter.str_to_dict(user.feature_vector)

        # 兴趣累加计算：User_New = User_Old + (Book_Vector * Weight)
        for tag_index, tfidf_val in book_vector.items():
            # 计算本次行为贡献的增量
            increment = tfidf_val * weight
            # 累加到用户对应的标签维度上
            current_val = user_vector_dict.get(tag_index, 0.0)
            user_vector_dict[tag_index] = current_val + increment

        # 写回数据库 此处为原始向量，在vector_utils有个方法会进行对数标准化,要使用用户的vector再调用它
        user.feature_vector = VectorConverter.dict_to_str(user_vector_dict)
        db.add(user)
        db.commit()