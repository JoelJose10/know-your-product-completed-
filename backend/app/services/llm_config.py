"""
Shared OpenAI / LiteLLM-compatible client configuration.

Uses OPENAI_API_KEY by default. Set OPENAI_BASE_URL to point at a
LiteLLM-compatible gateway (e.g. KeyValue) when running locally.
"""
import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv

load_dotenv()


def get_openai_api_key() -> Optional[str]:
    return os.getenv("OPENAI_API_KEY")


def get_openai_base_url() -> Optional[str]:
    """Return custom base URL if set; None means the official OpenAI API."""
    base_url = os.getenv("OPENAI_BASE_URL", "").strip()
    return base_url or None


def openai_client_kwargs() -> Dict[str, Any]:
    """Kwargs for openai.OpenAI(...)"""
    kwargs: Dict[str, Any] = {"api_key": get_openai_api_key()}
    base_url = get_openai_base_url()
    if base_url:
        kwargs["base_url"] = base_url
    return kwargs


def chat_openai_kwargs(
    model: str = "gpt-4o-mini",
    temperature: float = 0.3,
) -> Dict[str, Any]:
    """Kwargs for langchain_openai.ChatOpenAI(...)"""
    kwargs: Dict[str, Any] = {
        "model": model,
        "temperature": temperature,
        "api_key": get_openai_api_key(),
    }
    base_url = get_openai_base_url()
    if base_url:
        kwargs["base_url"] = base_url
    return kwargs


def is_openai_configured() -> bool:
    return bool(get_openai_api_key())
