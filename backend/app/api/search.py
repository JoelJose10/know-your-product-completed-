"""
Search API endpoint
Vector search inside one job's indexed documents
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional

from app.services.qdrant_client import search_vectors

router = APIRouter()


class SearchResult(BaseModel):
    chunk_id: str
    content: str
    score: float
    job_id: str
    source_file: Optional[str] = None


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total: int


@router.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(default=5, ge=1, le=20, description="Number of results"),
    job_id: str = Query(
        ...,
        min_length=1,
        description="Job ID whose documents to search"
    )
):
    """
    Search the vector database for relevant document chunks.
    Returns top matching results with similarity scores.
    """
    try:
        results = await search_vectors(
            query=q,
            limit=limit,
            job_id=job_id
        )
        
        search_results = [
            SearchResult(
                chunk_id=r["id"],
                content=r["content"],
                score=r["score"],
                job_id=r["job_id"],
                source_file=r.get("source_file")
            )
            for r in results
        ]
        
        return SearchResponse(
            query=q,
            results=search_results,
            total=len(search_results)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search error: {str(e)}"
        )
