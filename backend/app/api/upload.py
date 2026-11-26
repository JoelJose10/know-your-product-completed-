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


def safe_filename(filename: str | None) -> str | None:
    """Reduce a client-supplied filename to a plain name for the job directory."""
    name = os.path.basename((filename or "").replace("\\", "/").strip())
    if name in ("", ".", ".."):
        return None
    return name


def unique_name(name: str, used: set[str]) -> str:
    """Return a name that is not in used, so two uploads never share a path."""
    if name not in used:
        used.add(name)
        return name

    stem, ext = os.path.splitext(name)
    index = 1
    while f"{stem}-{index}{ext}" in used:
        index += 1
    unique = f"{stem}-{index}{ext}"
    used.add(unique)
    return unique


def safe_file_path(job_dir: str, name: str) -> str:
    """Build the stored path and refuse any path that leaves the job directory."""
    job_dir_abs = os.path.abspath(job_dir)
    file_path = os.path.abspath(os.path.join(job_dir_abs, name))
    if os.path.commonpath([job_dir_abs, file_path]) != job_dir_abs:
        raise HTTPException(status_code=400, detail=f"Invalid filename: {name}")
    return file_path


def validate_file(file: UploadFile) -> bool:
    """Validate file extension and size"""
    name = safe_filename(file.filename)
    if name is None:
        return False

    ext = os.path.splitext(name)[1].lower()
    return ext in ALLOWED_EXTENSIONS


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
    used_names: set[str] = set()
    for file in files:
        name = safe_filename(file.filename)
        if name is None:
            raise HTTPException(status_code=400, detail=f"Invalid filename: {file.filename!r}")

        name = unique_name(name, used_names)
        file_path = safe_file_path(job_dir, name)
        content = await file.read()
        
        # Check file size
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File {name} exceeds maximum size of 50MB"
            )
        
        with open(file_path, 'wb') as f:
            f.write(content)
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
