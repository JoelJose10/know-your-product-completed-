"""
Upload API endpoint
Handles file uploads and initiates background processing
"""
import uuid
import os
from typing import List
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from pydantic import BaseModel

from app.services.job_store import job_store, JobStatus
from app.workflows.pipeline import process_documents

router = APIRouter()

# Supported file types
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.md', '.txt', '.png', '.jpg', '.jpeg'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
READ_CHUNK_SIZE = 1024 * 1024  # Read uploads in 1MB windows so peak memory stays bounded

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
    
    ext = os.path.splitext(file.filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def size_limit_error(file: UploadFile) -> HTTPException:
    return HTTPException(
        status_code=400,
        detail=f"File {file.filename} exceeds maximum size of 50MB"
    )


async def save_upload(file: UploadFile, file_path: str) -> None:
    """Write one uploaded part to disk, rejecting it as soon as it passes MAX_FILE_SIZE"""
    written = 0
    try:
        with open(file_path, 'wb') as f:
            while True:
                chunk = await file.read(READ_CHUNK_SIZE)
                if not chunk:
                    break
                written += len(chunk)
                if written > MAX_FILE_SIZE:
                    raise size_limit_error(file)
                f.write(chunk)
    except BaseException:
        os.remove(file_path)
        raise


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
        raise HTTPException(status_code=400, detail="No files provided")
    
    # Validate files
    for file in files:
        if not validate_file(file):
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
    for file in files:
        if file.size is not None and file.size > MAX_FILE_SIZE:
            raise size_limit_error(file)
        
        file_path = os.path.join(job_dir, file.filename)
        await save_upload(file, file_path)
        saved_files.append(file_path)
    
    # Initialize job in store
    job_store.create_job(job_id, saved_files)
    
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
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobStatusResponse(
        job_id=job_id,
        status=job["status"],
        progress=job["progress"],
        message=job["message"],
        error=job.get("error")
    )
