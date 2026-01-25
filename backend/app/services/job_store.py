"""
Job Store Service
In-memory storage for job status and results
In production, this would be replaced with Redis or a database
"""
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
import threading


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobStore:
    """Thread-safe in-memory job storage"""
    
    def __init__(self):
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
    
    def create_job(self, job_id: str, files: List[str]) -> Dict[str, Any]:
        """Create a new job entry"""
        with self._lock:
            job = {
                "job_id": job_id,
                "status": JobStatus.PENDING,
                "progress": 0,
                "message": "Job created",
                "files": files,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "summary": None,
                "chunks": [],
                "error": None
            }
            self._jobs[job_id] = job
            return job
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job by ID"""
        with self._lock:
            return self._jobs.get(job_id)
    
    def update_job(
        self, 
        job_id: str, 
        status: Optional[JobStatus] = None,
        progress: Optional[int] = None,
        message: Optional[str] = None,
        summary: Optional[Dict] = None,
        chunks: Optional[List] = None,
        error: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Update job fields"""
        with self._lock:
            if job_id not in self._jobs:
                return None
            
            job = self._jobs[job_id]
            
            if status is not None:
                job["status"] = status
            if progress is not None:
                job["progress"] = progress
            if message is not None:
                job["message"] = message
            if summary is not None:
                job["summary"] = summary
            if chunks is not None:
                job["chunks"] = chunks
            if error is not None:
                job["error"] = error
            
            job["updated_at"] = datetime.utcnow().isoformat()
            
            return job
    
    def set_job_processing(self, job_id: str, message: str = "Processing..."):
        """Mark job as processing"""
        return self.update_job(
            job_id, 
            status=JobStatus.PROCESSING, 
            progress=10,
            message=message
        )
    
    def set_job_completed(self, job_id: str, summary: Dict, chunks: List = None):
        """Mark job as completed with results"""
        return self.update_job(
            job_id,
            status=JobStatus.COMPLETED,
            progress=100,
            message="Processing complete",
            summary=summary,
            chunks=chunks or []
        )
    
    def set_job_failed(self, job_id: str, error: str):
        """Mark job as failed"""
        return self.update_job(
            job_id,
            status=JobStatus.FAILED,
            message="Processing failed",
            error=error
        )
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a job"""
        with self._lock:
            if job_id in self._jobs:
                del self._jobs[job_id]
                return True
            return False
    
    def list_jobs(self) -> List[Dict[str, Any]]:
        """List all jobs"""
        with self._lock:
            return list(self._jobs.values())


# Global job store instance
job_store = JobStore()
