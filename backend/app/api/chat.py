"""Chat / question generation via Azure OpenAI (MIA agent)."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.services import azure_openai

router = APIRouter()


class ChatMessage(BaseModel):
    role: str  # "system" | "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    max_tokens: int = 1024
    temperature: float = 0.7


class ChatResponse(BaseModel):
    content: str


@router.post("/completions", response_model=ChatResponse)
async def chat_completions(body: ChatRequest):
    """Get a chat completion from Azure OpenAI (for MIA question generation / agent)."""
    if not settings.is_azure_openai_configured:
        raise HTTPException(
            status_code=503,
            detail="Azure OpenAI is not configured. Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY.",
        )
    messages = [{"role": m.role, "content": m.content} for m in body.messages]
    try:
        content = await azure_openai.chat_completion(
            messages,
            max_tokens=body.max_tokens,
            temperature=body.temperature,
        )
        return ChatResponse(content=content)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
