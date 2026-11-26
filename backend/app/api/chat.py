"""
Chat API endpoint
RAG-enabled chat for querying document content
"""
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.job_store import job_store
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
    # Reversible Polylane demo fault — set DEMO_FORCE_CHAT_ERROR=true on Render, then flip back to false.
    if os.getenv("DEMO_FORCE_CHAT_ERROR", "").lower() in ("1", "true", "yes"):
        raise HTTPException(
            status_code=500,
            detail="Demo fault: forced /chat failure for Polylane investigation",
        )

    job = job_store.get_job(request.job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] != "completed":
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
        
        return ChatResponse(
            response=result["response"],
            sources=result.get("sources", []),
            job_id=request.job_id
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating response: {str(e)}"
        )
