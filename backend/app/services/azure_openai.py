"""Azure OpenAI client for chat completions (MIA agent / question generation)."""
import asyncio
from openai import AzureOpenAI

from app.config import settings


def get_client() -> AzureOpenAI | None:
    if not settings.is_azure_openai_configured:
        return None
    return AzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint.rstrip("/"),
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
    )


def _chat_completion_sync(
    messages: list[dict[str, str]],
    *,
    deployment: str | None = None,
    max_tokens: int = 1024,
    temperature: float = 0.7,
) -> str:
    """Synchronous call to Azure OpenAI (run in thread)."""
    client = get_client()
    if not client:
        raise RuntimeError("Azure OpenAI is not configured (AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY).")

    model = deployment or settings.azure_openai_chat_deployment
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    if not response.choices:
        raise ValueError("No choices in Azure OpenAI response")
    return response.choices[0].message.content or ""


async def chat_completion(
    messages: list[dict[str, str]],
    *,
    deployment: str | None = None,
    max_tokens: int = 1024,
    temperature: float = 0.7,
) -> str:
    """Call Azure OpenAI chat completions and return the assistant message content."""
    return await asyncio.to_thread(
        _chat_completion_sync,
        messages,
        deployment=deployment,
        max_tokens=max_tokens,
        temperature=temperature,
    )
