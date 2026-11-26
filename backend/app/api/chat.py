"""
Chat API endpoint
RAG-enabled chat for querying document content
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.job_store import job_store
from app.services.logging_config import log_event, log_exception, update_request_context
from app.services.rag_service import rag_query

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    job_id: str
    conversation_history: Optional[list] = None


class ChatResponse(BaseModel):
    response: str
    sources: list = []
    job_id: str


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a chat message and get a RAG-enabled response.
    Uses the document content from the specified job for context.
    """
    update_request_context(job_id=request.job_id)
    message_length = len(request.message)
    history_length = len(request.conversation_history or [])

    job = job_store.get_job(request.job_id)

    if not job:
        log_event("job_not_found", level=logging.WARNING, endpoint="chat", message_length=message_length)
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] != "completed":
        log_event(
            "chat_rejected",
            level=logging.WARNING,
            job_status=job["status"],
            message_length=message_length,
            reason="job_not_completed",
        )
        raise HTTPException(
            status_code=400,
            detail="Document processing not complete. Please wait for processing to finish."
        )
    
    try:
        # Get RAG response
        result = await rag_query(
            query=request.message,
            job_id=request.job_id,
            conversation_history=request.conversation_history
        )
        
        log_event(
            "chat_answered",
            job_id=request.job_id,
            message_length=message_length,
            history_length=history_length,
            chunks_retrieved=result.get("chunks_retrieved"),
            source_count=len(result.get("sources") or []),
            answer_length=len(result.get("response") or ""),
        )
        
        return ChatResponse(
            response=result["response"],
            sources=result.get("sources", []),
            job_id=request.job_id
        )
        
    except Exception as e:
        log_exception(
            "chat_query_failed",
            e,
            job_id=request.job_id,
            message_length=message_length,
            history_length=history_length,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error generating response: {str(e)}"
        )
