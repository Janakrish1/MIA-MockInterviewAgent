"""Shared LLM for the interview graph (Azure OpenAI; later swappable for Gemma)."""
from langchain_openai import AzureChatOpenAI

from app.config import settings


def get_llm() -> AzureChatOpenAI:
    if not settings.is_azure_openai_configured:
        raise RuntimeError("Azure OpenAI is not configured.")
    return AzureChatOpenAI(
        azure_endpoint=settings.azure_openai_endpoint.rstrip("/"),
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        azure_deployment=settings.azure_openai_chat_deployment,
        temperature=1.0,
        max_tokens=1024,
    )
