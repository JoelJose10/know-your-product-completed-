"""
File name helpers shared by the upload API, the extraction service and the pipeline.
"""
import os


def file_extension(filename: str | None) -> str:
    """Return the lower-case extension of a file name, or an empty string."""
    return os.path.splitext(filename or "")[1].lower()
