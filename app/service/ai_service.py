# app/service/ai_service.py
from fastapi import Depends
from typing import AsyncGenerator
from app.dao.book_dao import BookDao
from app.core.llm_client import LLMClient, get_llm_client
from app.core.constants import PromptTemplates
from app.exceptions.book_exceptions import BookNotExistsException
from app.models import User
from app.recommend.matrix_cache import book_matrix_cache
from app.recommend.vector_utils import VectorConverter


class AIService:
    def __init__(
            self,
            book_dao: BookDao = Depends(),
            llm_client: LLMClient = Depends(get_llm_client)
    ):
        self.book_dao = book_dao
        self.llm_client = llm_client

    async def get_book_chat_stream(
            self,
            book_id: int,
            user_messages: list,
            enable_search: bool
    ) -> AsyncGenerator[str, None]:
        # 查数据库获取图书详情
        book = self.book_dao.get_book_by_id(book_id)
        if not book:
            raise BookNotExistsException()

        # 将书籍对象转为字典，构建 System Prompt
        system_content = PromptTemplates.build_book_system_prompt(book.model_dump())

        # 组装最终发送给大模型的 messages 数组
        full_messages = [{"role": "system", "content": system_content}]
        full_messages.extend(user_messages)  # 将前端传来的历史记录和当前问题追加进去

        # 调用 LLM 工具类，返回流式生成器
        async for chunk in self.llm_client.stream_chat(full_messages, enable_search):
            yield chunk

    async def get_recommend_reason_stream(self, book_id: int, current_user: User) -> AsyncGenerator[str, None]:
        """
        生成针对用户的专属流式推荐语
        """
        # 1. 查数据库获取图书详情
        book = self.book_dao.get_book_by_id(book_id)
        if not book:
            raise BookNotExistsException()

        matching_tag_names = []


        # 2. 核心逻辑：寻找共鸣标签 (要求用户有特征向量，且书籍在缓存中有向量)
        if current_user.feature_vector:
            user_vector_dict = VectorConverter.str_to_dict(current_user.feature_vector)
            book_vector_dict = book_matrix_cache.get_vector(book_id)

            if user_vector_dict and book_vector_dict:
                # 进行对数标准化以匹配推荐算法的真实权重分布
                normalized_user = VectorConverter.log_normalize(user_vector_dict)

                # 计算交集标签的乘积得分
                tag_scores = []
                for tag_index, user_val in normalized_user.items():
                    if tag_index in book_vector_dict:
                        score = user_val * book_vector_dict[tag_index]
                        tag_scores.append((tag_index, score))

                # 如果有共鸣点，按得分降序排，取出 Top 3 的 tag_index
                if tag_scores:
                    tag_scores.sort(key=lambda x: x[1], reverse=True)
                    top_3_indices = [item[0] for item in tag_scores[:3]]

                    # 3. 反向解析获取中文标签名称
                    matching_tag_names = self.book_dao.get_tag_names_by_indices(top_3_indices)

        import pprint
        pprint.pprint(matching_tag_names)

        # 4. 构建专门的 Prompt
        system_content = PromptTemplates.build_book_recommend_reason_prompt(
            book=book.model_dump(),
            matching_tags=matching_tag_names
        )

        # 5. 组装 Message 并调用流式返回 (无需历史记录)
        messages = [{"role": "user", "content": system_content}]

        # 推荐语不需要开启联网搜索，固定传 False 即可
        async for chunk in self.llm_client.stream_chat(messages, enable_search=False):
            yield chunk