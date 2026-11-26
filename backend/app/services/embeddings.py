"""
Embeddings Service
Generate embeddings using OpenAI API via Lite LLM
"""
import os
from typing import List
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize OpenAI client with Lite LLM configuration
LITE_LLM_BASE_URL = "https://llm.keyvalue.systems"
client = AsyncOpenAI(
    api_key=os.getenv("LITE_LLM_KEY"),
    base_url=LITE_LLM_BASE_URL
)

# Embedding model configuration
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536


async def generate_embedding(text: str) -> List[float]:
    """Generate embedding for a single text"""
    if not text or not text.strip():
        raise ValueError("Cannot generate embedding for empty text")
    
    # Truncate if too long (max ~8000 tokens for text-embedding-3-small)
    max_chars = 30000  # Approximate character limit
    if len(text) > max_chars:
        text = text[:max_chars]
    
    response = await client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
        dimensions=EMBEDDING_DIMENSIONS
    )
    
    return response.data[0].embedding


async def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for multiple texts in batch"""
    if not texts:
        return []
    
    # Filter and truncate texts
    max_chars = 30000
    processed_texts = []
    for text in texts:
        if text and text.strip():
            processed_texts.append(text[:max_chars] if len(text) > max_chars else text)
        else:
            processed_texts.append(" ")  # Placeholder for empty texts
    
    # OpenAI batch limit is 2048, process in batches if needed
    batch_size = 100
    all_embeddings = []
    
    for i in range(0, len(processed_texts), batch_size):
        batch = processed_texts[i:i + batch_size]
        
        response = await client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=batch,
            dimensions=EMBEDDING_DIMENSIONS
        )
        
        # Sort by index to maintain order
        sorted_data = sorted(response.data, key=lambda x: x.index)
        batch_embeddings = [item.embedding for item in sorted_data]
        all_embeddings.extend(batch_embeddings)
    
    return all_embeddings


def get_embedding_dimensions() -> int:
    """Return the embedding dimensions"""
    return EMBEDDING_DIMENSIONS
