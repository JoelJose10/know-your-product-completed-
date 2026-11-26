"""
Embeddings Service
OpenAI / OpenRouter embeddings via the shared LLM client config.
"""
from typing import List

from app.services.llm_config import (
    get_embedding_model_name,
    openai_client_kwargs,
)

EMBEDDING_DIMENSIONS = 1536

_client = None
_client_key = None


def _get_client():
    """Lazy OpenAI client; recreate if the resolved API key changes (e.g. after .env edit)."""
    global _client, _client_key
    from app.services.llm_config import get_openai_api_key

    key = get_openai_api_key()
    if _client is None or key != _client_key:
        from openai import OpenAI

        _client = OpenAI(**openai_client_kwargs())
        _client_key = key
    return _client


def _embedding_create_kwargs(input_value):
    """Build embeddings.create kwargs; dimensions only when using OpenAI-native models."""
    model = get_embedding_model_name()
    kwargs = {"model": model, "input": input_value}
    # OpenRouter/OpenAI text-embedding-3-* supports dimensions; skip for unknown models.
    if "text-embedding-3" in model:
        kwargs["dimensions"] = EMBEDDING_DIMENSIONS
    return kwargs


async def generate_embedding(text: str) -> List[float]:
    """Generate embedding for a single text"""
    if not text or not text.strip():
        raise ValueError("Cannot generate embedding for empty text")

    max_chars = 30000
    if len(text) > max_chars:
        text = text[:max_chars]

    client = _get_client()
    response = client.embeddings.create(**_embedding_create_kwargs(text))
    return response.data[0].embedding


async def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for multiple texts in batch"""
    if not texts:
        return []

    max_chars = 30000
    processed_texts = []
    for text in texts:
        if text and text.strip():
            processed_texts.append(text[:max_chars] if len(text) > max_chars else text)
        else:
            processed_texts.append(" ")

    client = _get_client()
    batch_size = 100
    all_embeddings: List[List[float]] = []

    for i in range(0, len(processed_texts), batch_size):
        batch = processed_texts[i : i + batch_size]
        response = client.embeddings.create(**_embedding_create_kwargs(batch))
        sorted_data = sorted(response.data, key=lambda x: x.index)
        all_embeddings.extend([item.embedding for item in sorted_data])

    return all_embeddings


def get_embedding_dimensions() -> int:
    """Return the embedding dimensions"""
    return EMBEDDING_DIMENSIONS
