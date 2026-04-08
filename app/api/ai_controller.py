# app/api/ai_controller.py
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.dependencies import get_current_user
from app.models import User
from app.schemas.ai_schema import AIChatRequestDTO
from app.service.ai_service import AIService

ai_router = APIRouter(prefix="/ai", tags=["AI大模型模块"])


@ai_router.post("/chat/book")
async def chat_about_book(
        ai_chat_request_dto: AIChatRequestDTO,
        current_user: User = Depends(get_current_user),
        service: AIService = Depends()
):
    """
    图书详情页的 AI 智能问答接口 (流式 SSE 返回)
    """
    # service 层的函数返回的是一个异步生成器
    generator = service.get_book_chat_stream(
        book_id=ai_chat_request_dto.book_id,
        user_messages=ai_chat_request_dto.messages,
        enable_search=ai_chat_request_dto.enable_search
    )

    # 必须指定 media_type="text/event-stream" ，这是前端接收流式数据的标准格式
    return StreamingResponse(generator, media_type="text/event-stream")