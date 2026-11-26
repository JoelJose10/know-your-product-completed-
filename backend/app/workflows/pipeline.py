"""
LangGraph Pipeline
Orchestrates the document processing workflow:
1. Extract text from files
2. Chunk content
3. Generate embeddings
4. Store in Qdrant
5. Generate product summary
"""
import logging
import os
import time
from typing import List, Dict, Any, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

from app.services.extraction import TextExtractor, TextChunker
from app.services.file_names import file_extension
from app.services.logging_config import log_event, log_exception
from app.services.qdrant_client import upsert_vectors
from app.services.job_store import job_store, JobStatus

load_dotenv()

# Initialize LLM with Lite LLM configuration
LITE_LLM_BASE_URL = "https://llm.keyvalue.systems"
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.3,
    api_key=os.getenv("LITE_LLM_KEY"),
    base_url=LITE_LLM_BASE_URL
)


class PipelineState(TypedDict):
    """State for the document processing pipeline"""
    job_id: str
    file_paths: List[str]
    extracted_documents: List[Dict[str, Any]]
    chunks: List[Dict[str, Any]]
    vectors_count: int
    summary: Dict[str, Any]
    error_message: str | None
    current_step: str


def extract_text_node(state: PipelineState) -> PipelineState:
    """Extract text from all uploaded files"""
    job_store.update_job(
        state["job_id"],
        status=JobStatus.PROCESSING,
        progress=20,
        message="Extracting text from documents..."
    )
    
    try:
        extractor = TextExtractor()
        documents = extractor.extract_multiple(state["file_paths"])
        
        # Check for extraction errors
        successful_docs = [d for d in documents if "error" not in d]
        failed_docs = [d for d in documents if "error" in d]
        if failed_docs:
            log_event(
                "pipeline_partial_extraction",
                level=logging.WARNING,
                job_id=state["job_id"],
                step="extract",
                document_count=len(documents),
                failed_document_count=len(failed_docs),
                failed_file_extensions=[file_extension(d.get("filename")) for d in failed_docs],
            )
        
        if not successful_docs:
            raise Exception("Failed to extract text from any document")
        
        return {
            **state,
            "extracted_documents": documents,
            "current_step": "chunk"
        }
    except Exception as e:
        log_exception(
            "pipeline_step_failed",
            e,
            job_id=state["job_id"],
            step="extract",
            file_count=len(state["file_paths"]),
        )
        return {
            **state,
            "error_message": f"Text extraction failed: {str(e)}",
            "current_step": "handle_error"
        }


def chunk_content_node(state: PipelineState) -> PipelineState:
    """Split extracted text into chunks"""
    job_store.update_job(
        state["job_id"],
        progress=40,
        message="Chunking content..."
    )
    
    try:
        chunker = TextChunker(chunk_size=1000, chunk_overlap=200)
        chunks = chunker.chunk_documents(state["extracted_documents"])
        
        if not chunks:
            raise Exception("No content chunks generated")
        
        return {
            **state,
            "chunks": chunks,
            "current_step": "embed"
        }
    except Exception as e:
        log_exception(
            "pipeline_step_failed",
            e,
            job_id=state["job_id"],
            step="chunk",
            document_count=len(state["extracted_documents"]),
        )
        return {
            **state,
            "error_message": f"Chunking failed: {str(e)}",
            "current_step": "handle_error"
        }


async def embed_and_store_node(state: PipelineState) -> PipelineState:
    """Generate embeddings and store in Qdrant"""
    job_store.update_job(
        state["job_id"],
        progress=60,
        message="Generating embeddings and storing vectors..."
    )
    
    try:
        vectors_count = await upsert_vectors(state["chunks"], state["job_id"])
        
        return {
            **state,
            "vectors_count": vectors_count,
            "current_step": "summarize"
        }
    except Exception as e:
        log_exception(
            "pipeline_step_failed",
            e,
            job_id=state["job_id"],
            step="embed",
            chunk_count=len(state["chunks"]),
        )
        return {
            **state,
            "error_message": f"Embedding/storage failed: {str(e)}",
            "current_step": "handle_error"
        }


async def generate_summary_node(state: PipelineState) -> PipelineState:
    """Generate product summary using LLM"""
    job_store.update_job(
        state["job_id"],
        progress=80,
        message="Generating product summary..."
    )
    all_content = ""

    try:
        # Combine all extracted content (truncate if too long)
        all_content = "\n\n---\n\n".join([
            f"[{doc.get('filename', 'Unknown')}]\n{doc.get('content', '')}"
            for doc in state["extracted_documents"]
            if "error" not in doc
        ])
        
        # Truncate to fit context window
        max_content_length = 50000
        if len(all_content) > max_content_length:
            all_content = all_content[:max_content_length] + "\n\n[Content truncated...]"
        
        # System prompt for summary generation
        system_prompt = """You are an expert product manager analyzing product documentation.
Given the following extracted content from PRDs, Figma exports, or screenshots, produce a comprehensive product summary.

Your summary should include:
1. Product purpose and value proposition (1-2 sentences)
2. Target users/audience
3. 3-5 main features or capabilities
4. Key metrics or success criteria (if mentioned)

Also extract:
- A concise title for the product
- 3-5 relevant tags/keywords
- A confidence score (0.0-1.0) based on how complete the documentation is

Format your response as follows:
TITLE: [Product title]
SUMMARY: [4-6 sentence summary]
TAGS: [comma-separated tags]
CONFIDENCE: [0.0-1.0]"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Here is the product documentation:\n\n{all_content}")
        ]
        
        response = await llm.ainvoke(messages)
        response_text = response.content
        
        # Parse response
        summary = parse_summary_response(response_text)
        
        return {
            **state,
            "summary": summary,
            "current_step": "complete"
        }
    except Exception as e:
        log_exception(
            "pipeline_step_failed",
            e,
            job_id=state["job_id"],
            step="summarize",
            chunk_count=len(state["chunks"]),
            content_char_count=len(all_content or ""),
        )
        return {
            **state,
            "error_message": f"Summary generation failed: {str(e)}",
            "current_step": "handle_error"
        }


def parse_summary_response(response_text: str) -> Dict[str, Any]:
    """Parse the LLM response into structured summary"""
    lines = response_text.strip().split('\n')
    
    title = "Product Summary"
    content = ""
    tags = []
    confidence = 0.8
    
    current_section = None
    summary_lines = []
    
    for line in lines:
        line = line.strip()
        if line.startswith("TITLE:"):
            title = line.replace("TITLE:", "").strip()
        elif line.startswith("SUMMARY:"):
            current_section = "summary"
            summary_lines.append(line.replace("SUMMARY:", "").strip())
        elif line.startswith("TAGS:"):
            current_section = "tags"
            tags_str = line.replace("TAGS:", "").strip()
            tags = [t.strip() for t in tags_str.split(",") if t.strip()]
        elif line.startswith("CONFIDENCE:"):
            current_section = "confidence"
            try:
                confidence = float(line.replace("CONFIDENCE:", "").strip())
            except ValueError:
                confidence = 0.8
        elif current_section == "summary" and line:
            summary_lines.append(line)
    
    content = " ".join(summary_lines)
    
    # Fallback if parsing failed
    if not content:
        content = response_text
    
    return {
        "title": title,
        "content": content,
        "tags": tags[:5],  # Limit to 5 tags
        "confidence": min(max(confidence, 0.0), 1.0)  # Clamp between 0 and 1
    }


def complete_node(state: PipelineState) -> PipelineState:
    """Mark job as complete"""
    job_store.set_job_completed(
        state["job_id"],
        summary=state["summary"],
        chunks=state["chunks"]
    )
    return state


def handle_error_node(state: PipelineState) -> PipelineState:
    """Handle pipeline errors"""
    job_store.set_job_failed(state["job_id"], state.get("error_message", "Unknown error"))
    return state


def route_next_step(state: PipelineState) -> str:
    """Route to next step based on current state"""
    if state.get("error_message"):
        return "handle_error"
    return state.get("current_step", "handle_error")


# Build the pipeline graph
def create_pipeline() -> StateGraph:
    """Create the LangGraph pipeline"""
    workflow = StateGraph(PipelineState)
    
    # Add nodes
    workflow.add_node("extract", extract_text_node)
    workflow.add_node("chunk", chunk_content_node)
    workflow.add_node("embed", embed_and_store_node)
    workflow.add_node("summarize", generate_summary_node)
    workflow.add_node("complete", complete_node)
    workflow.add_node("handle_error", handle_error_node)
    
    # Set entry point
    workflow.set_entry_point("extract")
    
    # Add edges
    workflow.add_conditional_edges(
        "extract",
        route_next_step,
        {
            "chunk": "chunk",
            "handle_error": "handle_error"
        }
    )
    
    workflow.add_conditional_edges(
        "chunk",
        route_next_step,
        {
            "embed": "embed",
            "handle_error": "handle_error"
        }
    )
    
    workflow.add_conditional_edges(
        "embed",
        route_next_step,
        {
            "summarize": "summarize",
            "handle_error": "handle_error"
        }
    )
    
    workflow.add_conditional_edges(
        "summarize",
        route_next_step,
        {
            "complete": "complete",
            "handle_error": "handle_error"
        }
    )
    
    workflow.add_edge("complete", END)
    workflow.add_edge("handle_error", END)
    
    return workflow.compile()


# Create pipeline instance
pipeline = create_pipeline()


def _job_status(job: Dict[str, Any]) -> str | None:
    """Return the status of a job as a plain string"""
    status = job.get("status")
    return getattr(status, "value", status)


async def process_documents(job_id: str, file_paths: List[str]):
    """
    Main entry point for document processing.
    Called as a background task from the upload endpoint.
    Emits exactly one terminal event per job, so that a failed job is visible
    without polling the job store.
    """
    initial_state: PipelineState = {
        "job_id": job_id,
        "file_paths": file_paths,
        "extracted_documents": [],
        "chunks": [],
        "vectors_count": 0,
        "summary": {},
        "error_message": None,
        "current_step": "extract"
    }

    started = time.perf_counter()
    log_event(
        "job_processing_started",
        job_id=job_id,
        file_count=len(file_paths),
        file_extensions=[file_extension(path) for path in file_paths],
    )

    try:
        # Run the pipeline
        final_state = await pipeline.ainvoke(initial_state)
    except Exception as e:
        # Catch any unhandled errors
        job_store.set_job_failed(job_id, f"Pipeline error: {str(e)}")
        log_exception(
            "job_processing_failed",
            e,
            job_id=job_id,
            duration_ms=round((time.perf_counter() - started) * 1000, 2),
            failure_stage="pipeline_invocation",
            file_count=len(file_paths),
        )
        return

    duration_ms = round((time.perf_counter() - started) * 1000, 2)
    job = job_store.get_job(job_id) or {}
    summary = final_state.get("summary") or {}
    terminal_fields = {
        "job_id": job_id,
        "duration_ms": duration_ms,
        "file_count": len(file_paths),
        "chunk_count": len(final_state.get("chunks") or []),
        "vector_count": final_state.get("vectors_count"),
        "job_status": _job_status(job),
    }

    if final_state.get("error_message"):
        log_event(
            "job_processing_failed",
            level=logging.ERROR,
            failure_stage="pipeline_step",
            job_error=final_state.get("error_message"),
            **terminal_fields,
        )
        return

    log_event(
        "job_processing_completed",
        summary_confidence=summary.get("confidence"),
        summary_tag_count=len(summary.get("tags") or []),
        **terminal_fields,
    )
