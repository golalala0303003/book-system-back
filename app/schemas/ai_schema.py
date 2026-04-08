from pydantic import BaseModel, Field
from typing import List, Dict

class AIChatRequestDTO(BaseModel):
    book_id: int = Field(..., description="正在咨询的图书ID")
    messages: List[Dict[str, str]] = Field(
        ...,
        description="对话历史与当前问题，格式如 [{'role': 'user', 'content': '这书适合谁看？'}]"
    )
    enable_search: bool = Field(default=False, description="是否开启大模型联网搜索")