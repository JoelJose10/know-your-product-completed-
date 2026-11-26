"""
Search API endpoint
Vector search across all indexed documents
"""
import logging
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional

from app.services.logging_config import log_event, log_exception, update_request_context
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
    job_id: Optional[str] = Query(default=None, description="Filter by job ID")
):
    """
    Search the vector database for relevant document chunks.
    Returns top matching results with similarity scores.
    """
    if job_id:
        update_request_context(job_id=job_id)
    query_length = len(q)

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
        
        log_event(
            "search_completed",
            job_id=job_id,
            query_length=query_length,
            limit=limit,
            result_count=len(search_results),
            top_score=round(search_results[0].score, 3) if search_results else None,
        )
        
        return SearchResponse(
            query=q,
            results=search_results,
            total=len(search_results)
        )
        
    except Exception as e:
        log_exception(
            "search_query_failed",
            e,
            job_id=job_id,
            query_length=query_length,
            limit=limit,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Search error: {str(e)}"
        )
