"""
Embeddings Service
Generate embeddings using OpenAI (or mock vectors when MOCK_LLM=true)
"""
from typing import List, Optional

from app.services.llm_config import openai_client_kwargs, use_mock_llm

# Embedding model configuration
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536

_client = None


def _get_client():
    global _client
    if use_mock_llm():
        return None
    if _client is None:
        from openai import OpenAI

        _client = OpenAI(**openai_client_kwargs())
    return _client


async def generate_embedding(text: str) -> List[float]:
    """Generate embedding for a single text"""
    if not text or not text.strip():
        raise ValueError("Cannot generate embedding for empty text")

    max_chars = 30000
    if len(text) > max_chars:
        text = text[:max_chars]

    if use_mock_llm():
        from app.services.mock_llm import mock_embedding

        return mock_embedding(text, EMBEDDING_DIMENSIONS)

    client = _get_client()
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
        dimensions=EMBEDDING_DIMENSIONS,
    )
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

    if use_mock_llm():
        from app.services.mock_llm import mock_embeddings_batch

        return mock_embeddings_batch(processed_texts)

    client = _get_client()
    batch_size = 100
    all_embeddings: List[List[float]] = []

    for i in range(0, len(processed_texts), batch_size):
        batch = processed_texts[i : i + batch_size]
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=batch,
            dimensions=EMBEDDING_DIMENSIONS,
        )
        sorted_data = sorted(response.data, key=lambda x: x.index)
        all_embeddings.extend([item.embedding for item in sorted_data])

    return all_embeddings


def get_embedding_dimensions() -> int:
    """Return the embedding dimensions"""
    return EMBEDDING_DIMENSIONS
