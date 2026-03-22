from __future__ import annotations

import csv
import logging
import re
import time
import uuid
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)
SYSTEM_LOG_DIR = Path("system_log")
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def sanitize_request_id(request_id: str) -> str:
    """Validate request IDs used in filesystem paths and API routing."""
    if not request_id or not REQUEST_ID_PATTERN.fullmatch(request_id):
        raise ValueError("Invalid request_id format")
    return request_id


def ensure_request_log_file(request_id: str) -> Path:
    """Create the request log file and CSV header if missing."""
    safe_request_id = sanitize_request_id(request_id)
    SYSTEM_LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = SYSTEM_LOG_DIR / f"request_{safe_request_id}.csv"
    if not log_file.exists():
        with log_file.open("w", newline="", encoding="utf-8") as file_pointer:
            writer = csv.writer(file_pointer)
            writer.writerow(["Timestamp", "Status", "Message"])
    return log_file

def log_to_request_file(request_id: str, status: str, message: str) -> None:
    """Log message to request-specific CSV file without console output.
    
    Args:
        request_id: The request ID.
        status: The current status.
        message: The message to log.
    """
    if not request_id:
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        log_file = ensure_request_log_file(request_id)
        with log_file.open("a", newline="", encoding="utf-8") as file_pointer:
            writer = csv.writer(file_pointer)
            writer.writerow([timestamp, status, message])
    except Exception as e:
        # Only log errors to console, not the actual messages
        logger.error(f"Error writing to request log file: {str(e)}")

def retry_with_backoff(max_retries=3, initial_delay=1, max_delay=10):
    """Decorator for retrying functions with exponential backoff"""
    def decorator(func: Callable[..., Any]):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        msg = f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {delay} seconds..."
                        logger.warning(msg)
                        # Try to get request_id from args or kwargs
                        request_id = getattr(args[0], 'current_request_id', None) if args else None
                        if request_id:
                            log_to_request_file(request_id, "retry", msg)
                        time.sleep(delay)
                        delay = min(delay * 2, max_delay)
                    else:
                        msg = f"All {max_retries} attempts failed. Last error: {str(e)}"
                        logger.error(msg)
                        request_id = getattr(args[0], 'current_request_id', None) if args else None
                        if request_id:
                            log_to_request_file(request_id, "error", msg)
                        raise last_exception
            
            return None
        return wrapper
    return decorator

def initialize_request() -> str:
    """Initialize a new request with a unique ID"""
    request_id = f"{datetime.now().strftime('%Y%m%d')}_{str(uuid.uuid4())[:8]}"

    try:
        ensure_request_log_file(request_id)
    except Exception as e:
        logger.error(f"Error creating request log file: {str(e)}")
    return request_id
