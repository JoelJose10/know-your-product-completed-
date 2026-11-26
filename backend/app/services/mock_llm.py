"""
Free mock LLM + embeddings for demos without a paid OpenAI key.

Enable with MOCK_LLM=true (used on Render free demo by default).
"""
from __future__ import annotations

import hashlib
import math
import re
from typing import Any, List, Sequence

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage


EMBEDDING_DIMENSIONS = 1536


def mock_embedding(text: str, dimensions: int = EMBEDDING_DIMENSIONS) -> List[float]:
    """Deterministic pseudo-embedding from text (good enough for demo RAG)."""
    if not text or not text.strip():
        text = " "
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values: List[float] = []
    seed = digest
    while len(values) < dimensions:
        seed = hashlib.sha256(seed).digest()
        for b in seed:
            # map byte to [-1, 1]
            values.append((b / 127.5) - 1.0)
            if len(values) >= dimensions:
                break
    # L2 normalize
    norm = math.sqrt(sum(v * v for v in values)) or 1.0
    return [v / norm for v in values]


def mock_embeddings_batch(texts: Sequence[str]) -> List[List[float]]:
    return [mock_embedding(t) for t in texts]


class MockChatModel:
    """Minimal async chat stand-in with ainvoke(messages) -> AIMessage."""

    async def ainvoke(self, messages: Sequence[BaseMessage], **_: Any) -> AIMessage:
        human_bits = [
            m.content for m in messages if isinstance(m, HumanMessage) and isinstance(m.content, str)
        ]
        blob = "\n".join(human_bits)
        lower = blob.lower()

        if "follow-up questions" in lower or "generate" in lower and "questions" in lower:
            return AIMessage(
                content=(
                    "1. Who is the primary target user?\n"
                    "2. What are the main features?\n"
                    "3. How is success measured?"
                )
            )

        if "TITLE:" in blob or "product documentation" in lower or "product summary" in lower:
            title = _guess_title(blob)
            snippet = _snippet(blob, 400)
            return AIMessage(
                content=(
                    f"TITLE: {title}\n"
                    f"SUMMARY: {snippet} This mock summary was generated without a paid OpenAI key "
                    f"so the Render/Polylane demo can run for free.\n"
                    f"TAGS: demo, mock-llm, product, render\n"
                    f"CONFIDENCE: 0.55"
                )
            )

        # Default RAG-style answer from retrieved context in the prompt
        context = _snippet(blob, 600)
        question = _last_question(blob)
        return AIMessage(
            content=(
                f"Based on the uploaded documents (mock LLM):\n\n"
                f"**Question:** {question}\n\n"
                f"**Answer:** {context if context else 'No context was retrieved for this question.'}\n\n"
                f"_Running in MOCK_LLM mode — no paid OpenAI credits required._"
            )
        )


def _guess_title(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("Here is") or line.startswith("["):
            continue
        if len(line) > 8:
            return line[:80]
    return "Product Summary (Mock)"


def _snippet(text: str, limit: int) -> str:
    # Prefer content after documentation markers
    cleaned = re.sub(r"\s+", " ", text).strip()
    if "Here is the product documentation:" in cleaned:
        cleaned = cleaned.split("Here is the product documentation:", 1)[-1].strip()
    if "Context from uploaded documents:" in cleaned:
        cleaned = cleaned.split("Context from uploaded documents:", 1)[-1]
        if "User Question:" in cleaned:
            cleaned = cleaned.split("User Question:", 1)[0]
    cleaned = cleaned.strip()
    if len(cleaned) > limit:
        return cleaned[:limit].rstrip() + "…"
    return cleaned or "Documentation was uploaded successfully."


def _last_question(text: str) -> str:
    if "User Question:" in text:
        return text.split("User Question:", 1)[-1].strip().split("\n")[0][:200]
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return lines[-1][:200] if lines else "What is this product?"
