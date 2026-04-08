# app/service/ai_service.py
from fastapi import Depends
from typing import AsyncGenerator
from app.dao.book_dao import BookDao
from app.core.llm_client import LLMClient, get_llm_client
from app.core.constants import PromptTemplates
from app.exceptions.book_exceptions import BookNotExistsException


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