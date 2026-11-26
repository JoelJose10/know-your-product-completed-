"""
LangSmith Tracing Configuration
Sets up observability for LangGraph pipelines and LLM calls
"""
import logging
import os
from dotenv import load_dotenv

from app.services.logging_config import log_event

load_dotenv()


def configure_langsmith():
    """
    Configure LangSmith tracing.
    Environment variables should be set in .env file:
    - LANGCHAIN_API_KEY: Your LangSmith API key
    - LANGCHAIN_TRACING_V2: Set to "true" to enable tracing
    - LANGCHAIN_PROJECT: Project name in LangSmith
    """
    # Check if tracing is enabled
    tracing_enabled = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    api_key = os.getenv("LANGCHAIN_API_KEY")
    project = os.getenv("LANGCHAIN_PROJECT", "know-your-product")
    
    if tracing_enabled and api_key:
        # Set environment variables for LangChain/LangGraph
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = api_key
        os.environ["LANGCHAIN_PROJECT"] = project
        os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
        
        log_event(
            "langsmith_tracing_configured",
            enabled=True,
            project=project,
            api_key_set=True,
            endpoint="https://api.smith.langchain.com",
        )
        return True
    else:
        reason = "api_key_missing" if tracing_enabled else "disabled_by_config"
        log_event(
            "langsmith_tracing_configured",
            level=logging.WARNING if tracing_enabled else logging.INFO,
            enabled=False,
            project=project,
            api_key_set=bool(api_key),
            reason=reason,
        )
        return False


def get_tracing_status() -> dict:
    """Get current tracing configuration status"""
    return {
        "enabled": os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true",
        "project": os.getenv("LANGCHAIN_PROJECT", "know-your-product"),
        "api_key_set": bool(os.getenv("LANGCHAIN_API_KEY"))
    }
