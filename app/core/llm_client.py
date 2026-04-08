from typing import AsyncGenerator, List, Dict, Any
from openai import AsyncOpenAI
from app.core.config import settings
from app.exceptions.llm_exceptions import LLMNotAvailableException


class LLMClient:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL
        )
        self.model_name = settings.LLM_MODEL_NAME

    async def stream_chat(self,
        messages: List[Dict[str, Any]],
        enable_search: bool = False
    ) -> AsyncGenerator[str, None]:
        """
        发起流式对话请求 (强制流式)
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                stream=True,
                extra_body={"enable_search": enable_search,
                            "enable_thinking": False}
            )

            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            print(f"LLM Stream API 请求异常: {str(e)}") # 记录原始日志
            raise LLMNotAvailableException()

_llm_client_instance = LLMClient()

def get_llm_client() -> LLMClient:
    return _llm_client_instance