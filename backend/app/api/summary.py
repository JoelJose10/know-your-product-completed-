"""
Summary API endpoint
Returns product summaries for processed jobs
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from app.services.job_store import job_store
from app.services.logging_config import log_event, update_request_context

router = APIRouter()


class SummaryResponse(BaseModel):
    job_id: str
    title: Optional[str] = None
    content: str
    tags: List[str] = []
    confidence: Optional[float] = None
    source_files: List[str] = []


@router.get("/summary/{job_id}", response_model=SummaryResponse)
async def get_summary(job_id: str):
    """
    Get the product summary for a completed job.
    Returns summary content, title, tags, and confidence score.
    """
    update_request_context(job_id=job_id)
    job = job_store.get_job(job_id)

    if not job:
        log_event("job_not_found", level=logging.WARNING, job_id=job_id, endpoint="summary")
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] != "completed":
        log_event(
            "summary_rejected",
            level=logging.WARNING,
            job_id=job_id,
            job_status=job["status"],
            reason="job_not_completed",
        )
        raise HTTPException(
            status_code=400, 
            detail=f"Job is not completed. Current status: {job['status']}"
        )
    
    summary = job.get("summary", {})
    
    return SummaryResponse(
        job_id=job_id,
        title=summary.get("title", "Product Summary"),
        content=summary.get("content", "No summary available"),
        tags=summary.get("tags", []),
        confidence=summary.get("confidence"),
        source_files=[f.split('/')[-1] for f in job.get("files", [])]
    )
