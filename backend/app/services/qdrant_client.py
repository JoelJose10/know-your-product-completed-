"""
Qdrant Client Service
Vector database operations for storing and searching embeddings
"""
import os
import uuid
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from dotenv import load_dotenv

from app.services.embeddings import generate_embedding, generate_embeddings_batch, EMBEDDING_DIMENSIONS

load_dotenv()

# Qdrant configuration
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = "know_your_product"

# Global client instance
_client: Optional[QdrantClient] = None


async def init_qdrant():
    """Initialize Qdrant client and create collection if needed"""
    global _client
    
    if QDRANT_API_KEY:
        # Cloud connection
        _client = QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
        )
    else:
        # Local connection
        _client = QdrantClient(url=QDRANT_URL)
    
    # Check if collection exists, create if not
    collections = _client.get_collections().collections
    collection_names = [c.name for c in collections]
    
    if COLLECTION_NAME not in collection_names:
        _client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=EMBEDDING_DIMENSIONS,
                distance=Distance.COSINE
            )
        )
        print(f"✅ Created collection: {COLLECTION_NAME}")
    else:
        print(f"✅ Collection exists: {COLLECTION_NAME}")


def get_client() -> QdrantClient:
    """Get the Qdrant client instance"""
    global _client
    if _client is None:
        raise RuntimeError("Qdrant client not initialized. Call init_qdrant() first.")
    return _client


async def upsert_vectors(
    chunks: List[Dict[str, Any]], 
    job_id: str
) -> int:
    """
    Generate embeddings and upsert vectors to Qdrant.
    Returns number of vectors upserted.
    """
    client = get_client()
    
    if not chunks:
        return 0
    
    # Extract texts for embedding
    texts = [chunk.get("content", "") for chunk in chunks]
    
    # Generate embeddings in batch
    embeddings = await generate_embeddings_batch(texts)
    
    # Create points
    points = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        point_id = str(uuid.uuid4())
        
        payload = {
            "job_id": job_id,
            "content": chunk.get("content", ""),
            "chunk_index": chunk.get("index", i),
            "filename": chunk.get("filename", ""),
            "file_type": chunk.get("file_type", ""),
            "start_char": chunk.get("start_char", 0),
            "end_char": chunk.get("end_char", 0),
        }
        
        points.append(PointStruct(
            id=point_id,
            vector=embedding,
            payload=payload
        ))
    
    # Upsert in batches
    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=batch
        )
    
    return len(points)


async def search_vectors(
    query: str,
    limit: int = 5,
    job_id: Optional[str] = None,
    score_threshold: float = 0.5
) -> List[Dict[str, Any]]:
    """
    Search for similar vectors in Qdrant using query_points API.
    Returns list of matching chunks with scores.
    
    Reference: https://qdrant.tech/documentation/quickstart/
    """
    client = get_client()
    
    # Generate query embedding
    query_embedding = await generate_embedding(query)
    
    # Build filter if job_id specified
    query_filter = None
    if job_id:
        query_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="job_id",
                    match=models.MatchValue(value=job_id)
                )
            ]
        )
    
    # Use query_points (newer API) for search
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding,
        query_filter=query_filter,
        limit=limit,
        score_threshold=score_threshold,
        with_payload=True
    ).points
    
    # Format results
    formatted_results = []
    for result in results:
        formatted_results.append({
            "id": str(result.id),
            "score": result.score,
            "content": result.payload.get("content", ""),
            "job_id": result.payload.get("job_id", ""),
            "source_file": result.payload.get("filename", ""),
            "chunk_index": result.payload.get("chunk_index", 0)
        })
    
    return formatted_results


async def delete_job_vectors(job_id: str) -> int:
    """Delete all vectors for a specific job"""
    client = get_client()
    
    result = client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="job_id",
                        match=models.MatchValue(value=job_id)
                    )
                ]
            )
        )
    )
    
    return result


async def get_collection_info() -> Dict[str, Any]:
    """Get information about the collection"""
    client = get_client()
    
    info = client.get_collection(collection_name=COLLECTION_NAME)
    
    return {
        "name": COLLECTION_NAME,
        "vectors_count": info.vectors_count,
        "points_count": info.points_count,
        "status": info.status
    }
