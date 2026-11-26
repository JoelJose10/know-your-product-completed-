"""
Shared LLM client configuration.

Priority:
1. OPENROUTER_API_KEY → OpenRouter (OpenAI-compatible)
2. OPENAI_API_KEY (+ optional OPENAI_BASE_URL for LiteLLM / OpenAI)
"""
import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv

load_dotenv()

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_CHAT_MODEL = "openai/gpt-4o-mini"
DEFAULT_EMBEDDING_MODEL = "openai/text-embedding-3-small"


def _is_openrouter_base(url: Optional[str]) -> bool:
    return bool(url) and "openrouter.ai" in url


def get_openai_base_url() -> Optional[str]:
    """Return API base URL. OpenRouter is used automatically when its key is set."""
    explicit = os.getenv("OPENAI_BASE_URL", "").strip()
    if explicit:
        return explicit
    if os.getenv("OPENROUTER_API_KEY", "").strip():
        return OPENROUTER_BASE_URL
    # Legacy KeyValue LiteLLM when only LITE_LLM_KEY is present
    if os.getenv("LITE_LLM_KEY", "").strip() and not os.getenv("OPENAI_API_KEY", "").strip():
        return "https://llm.keyvalue.systems"
    return None


def get_openai_api_key() -> Optional[str]:
    """
    Resolve the API key for the active base URL.

    When talking to OpenRouter, only OPENROUTER_API_KEY is accepted so a leftover
    OPENAI_API_KEY / LITE_LLM_KEY cannot be sent and trigger a 401.
    """
    base = get_openai_base_url()
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()

    if _is_openrouter_base(base) or openrouter_key:
        return openrouter_key or None

    return (
        os.getenv("OPENAI_API_KEY", "").strip()
        or os.getenv("LITE_LLM_KEY", "").strip()
        or None
    )


def get_chat_model_name() -> str:
    return os.getenv("CHAT_MODEL", DEFAULT_CHAT_MODEL).strip() or DEFAULT_CHAT_MODEL


def get_embedding_model_name() -> str:
    return (
        os.getenv("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL).strip()
        or DEFAULT_EMBEDDING_MODEL
    )


def _default_headers() -> Dict[str, str]:
    """OpenRouter optionally uses these headers for rankings / app attribution."""
    headers: Dict[str, str] = {}
    referer = os.getenv("OPENROUTER_HTTP_REFERER", "").strip()
    title = os.getenv("OPENROUTER_APP_TITLE", "Know Your Product").strip()
    if _is_openrouter_base(get_openai_base_url()) or os.getenv("OPENROUTER_API_KEY"):
        if referer:
            headers["HTTP-Referer"] = referer
        if title:
            headers["X-Title"] = title
    return headers


def openai_client_kwargs() -> Dict[str, Any]:
    """Kwargs for openai.OpenAI(...)"""
    key = get_openai_api_key()
    base_url = get_openai_base_url()
    if _is_openrouter_base(base_url) and not key:
        raise RuntimeError(
            "OPENAI_BASE_URL points at OpenRouter but OPENROUTER_API_KEY is missing. "
            'OpenRouter keys start with "sk-or-".'
        )
    if not key:
        raise RuntimeError("Set OPENROUTER_API_KEY (or OPENAI_API_KEY) before using the LLM")
    kwargs: Dict[str, Any] = {"api_key": key}
    if base_url:
        kwargs["base_url"] = base_url
    headers = _default_headers()
    if headers:
        kwargs["default_headers"] = headers
    return kwargs


def chat_openai_kwargs(temperature: float = 0.3) -> Dict[str, Any]:
    """Kwargs for langchain_openai.ChatOpenAI(...)"""
    key = get_openai_api_key()
    base_url = get_openai_base_url()
    if _is_openrouter_base(base_url) and not key:
        raise RuntimeError(
            "OPENAI_BASE_URL points at OpenRouter but OPENROUTER_API_KEY is missing. "
            'OpenRouter keys start with "sk-or-".'
        )
    if not key:
        raise RuntimeError("Set OPENROUTER_API_KEY (or OPENAI_API_KEY) before using the LLM")
    kwargs: Dict[str, Any] = {
        "model": get_chat_model_name(),
        "temperature": temperature,
        "api_key": key,
    }
    if base_url:
        kwargs["base_url"] = base_url
    headers = _default_headers()
    if headers:
        kwargs["default_headers"] = headers
    return kwargs


def get_chat_model():
    """Return ChatOpenAI configured for OpenRouter / OpenAI."""
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(**chat_openai_kwargs())


def is_llm_configured() -> bool:
    return bool(get_openai_api_key())


# Back-compat alias
def is_openai_configured() -> bool:
    return is_llm_configured()
