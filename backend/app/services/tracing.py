"""
LangSmith Tracing Configuration
Sets up observability for LangGraph pipelines and LLM calls
"""
import os
from dotenv import load_dotenv

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
        
        print(f"✅ LangSmith tracing enabled for project: {project}")
        return True
    else:
        if tracing_enabled and not api_key:
            print("⚠️ LangSmith tracing enabled but LANGCHAIN_API_KEY not set")
        else:
            print("ℹ️ LangSmith tracing disabled")
        return False


def get_tracing_status() -> dict:
    """Get current tracing configuration status"""
    return {
        "enabled": os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true",
        "project": os.getenv("LANGCHAIN_PROJECT", "know-your-product"),
        "api_key_set": bool(os.getenv("LANGCHAIN_API_KEY"))
    }
