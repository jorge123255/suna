from fastapi import HTTPException, Request, Depends
from typing import Optional, List, Dict, Any
import uuid
from utils.logger import logger as app_logger

# This function always returns a default user ID without checking JWT
async def get_current_user_id_from_jwt(request: Request) -> str:
    """
    In local server mode, always return a default user ID without checking JWT.
    
    Args:
        request: The FastAPI request object
        
    Returns:
        str: A default user ID for local server mode
    """
    # Return a default user ID for local server mode
    default_user_id = "00000000-0000-0000-0000-000000000001"
    app_logger.info(f"Local server mode: Using default user ID: {default_user_id}")
    return default_user_id

async def get_account_id_from_thread(client, thread_id: str) -> str:
    """
    In local server mode, always return a default account ID.
    
    Args:
        client: The Supabase client
        thread_id: The ID of the thread
        
    Returns:
        str: A default account ID for local server mode
    """
    # Return a default account ID for local server mode
    default_account_id = "00000000-0000-0000-0000-000000000000"
    app_logger.info(f"Local server mode: Using default account ID: {default_account_id}")
    return default_account_id
    
async def get_user_id_from_stream_auth(
    request: Request,
    token: Optional[str] = None
) -> str:
    """
    In local server mode, always return a default user ID without checking authentication.
    
    Args:
        request: The FastAPI request object
        token: Optional token from query parameters (ignored)
        
    Returns:
        str: A default user ID for local server mode
    """
    # Return a default user ID for local server mode
    default_user_id = "00000000-0000-0000-0000-000000000001"
    app_logger.info(f"Local server mode: Using default user ID for stream: {default_user_id}")
    return default_user_id
async def verify_thread_access(client, thread_id: str, user_id: str):
    """
    Verify that the user has access to the thread.
    In local server mode, always allow access.
    """
    # Always allow access in local server mode
    app_logger.info(f"Local server mode: Bypassing authentication for thread access to {thread_id}")
    return True

async def get_optional_user_id(request: Request) -> Optional[str]:
    """
    In local server mode, always return a default user ID.
    
    Args:
        request: The FastAPI request object
        
    Returns:
        str: A default user ID for local server mode
    """
    # Return a default user ID for local server mode
    default_user_id = "00000000-0000-0000-0000-000000000001"
    app_logger.info(f"Local server mode: Using default user ID for optional auth: {default_user_id}")
    return default_user_id
