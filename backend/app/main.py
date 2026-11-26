"""
Know Your Product - FastAPI Backend
Main application entry point
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.api import upload, summary, chat, search
from app.services.tracing import configure_langsmith

# Load environment variables
load_dotenv()

# Configure LangSmith tracing
configure_langsmith()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events"""
    # Startup: Initialize services
    from app.services.qdrant_client import init_qdrant, close_qdrant
    await init_qdrant()
    print("✅ Qdrant client initialized")
    
    yield
    
    # Shutdown: Cleanup
    await close_qdrant()
    print("👋 Shutting down...")

app = FastAPI(
    title="Know Your Product API",
    description="AI-powered product documentation analysis and chat",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router, tags=["Upload"])
app.include_router(summary.router, tags=["Summary"])
app.include_router(chat.router, tags=["Chat"])
app.include_router(search.router, tags=["Search"])

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Know Your Product API",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    from app.services.tracing import get_tracing_status
    
    return {
        "status": "healthy",
        "qdrant": "connected",
        "lite_llm": "configured" if os.getenv("LITE_LLM_KEY") else "not configured",
        "langsmith": get_tracing_status()
    }
