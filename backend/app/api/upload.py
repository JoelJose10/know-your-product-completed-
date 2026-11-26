"""
Upload API endpoint
Handles file uploads and initiates background processing
"""
import logging
import uuid
import os
from typing import List
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from pydantic import BaseModel

from app.services.file_names import file_extension
from app.services.job_store import job_store, JobStatus
from app.services.logging_config import log_event, update_request_context
from app.workflows.pipeline import process_documents

router = APIRouter()

# Supported file types
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.md', '.txt', '.png', '.jpg', '.jpeg'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Upload directory
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)


class UploadResponse(BaseModel):
    job_id: str
    status: str
    message: str
    files_received: int


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: int
    message: str
    error: str | None = None


def validate_file(file: UploadFile) -> bool:
    """Validate file extension and size"""
    if not file.filename:
        return False
    
    return file_extension(file.filename) in ALLOWED_EXTENSIONS


@router.post("/upload", response_model=UploadResponse)
async def upload_files(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...)
):
    """
    Upload one or more files for processing.
    Returns a job_id to track processing status.
    """
    if not files:
        log_event(
            "upload_rejected",
            level=logging.WARNING,
            reason="no_files",
        )
        raise HTTPException(status_code=400, detail="No files provided")
    
    # Validate files
    for index, file in enumerate(files):
        if not validate_file(file):
            extension = file_extension(file.filename)
            log_event(
                "upload_rejected",
                level=logging.WARNING,
                reason="unsupported_extension" if file.filename else "missing_filename",
                file_index=index,
                file_extension=extension,
                file_count=len(files),
                allowed_extensions=sorted(ALLOWED_EXTENSIONS),
            )
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type: {file.filename}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Create job directory
    job_dir = os.path.join(UPLOAD_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)
    
    # Save files
    saved_files = []
    saved_bytes = 0
    for index, file in enumerate(files):
        file_path = os.path.join(job_dir, file.filename)
        content = await file.read()
        
        # Check file size
        if len(content) > MAX_FILE_SIZE:
            log_event(
                "upload_rejected",
                level=logging.WARNING,
                reason="file_too_large",
                job_id=job_id,
                file_index=index,
                file_extension=file_extension(file.filename),
                file_size_bytes=len(content),
                max_file_size_bytes=MAX_FILE_SIZE,
                file_count=len(files),
            )
            raise HTTPException(
                status_code=400,
                detail=f"File {file.filename} exceeds maximum size of 50MB"
            )
        
        with open(file_path, 'wb') as f:
            f.write(content)
        saved_files.append(file_path)
        saved_bytes += len(content)
    
    # Initialize job in store
    job_store.create_job(job_id, saved_files)
    update_request_context(job_id=job_id)
    
    log_event(
        "upload_accepted",
        job_id=job_id,
        file_count=len(saved_files),
        total_bytes=saved_bytes,
        file_extensions=sorted({file_extension(f) for f in saved_files}),
    )
    
    # Start background processing
    background_tasks.add_task(process_documents, job_id, saved_files)
    
    return UploadResponse(
        job_id=job_id,
        status="processing",
        message=f"Processing {len(files)} file(s)",
        files_received=len(files)
    )


@router.get("/job/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Get the current status of a processing job"""
    job = job_store.get_job(job_id)
    
    if not job:
        log_event(
            "job_not_found",
            level=logging.WARNING,
            job_id=job_id,
            endpoint="job_status",
        )
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobStatusResponse(
        job_id=job_id,
        status=job["status"],
        progress=job["progress"],
        message=job["message"],
        error=job.get("error")
    )
