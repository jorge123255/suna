"""
Comprehensive logger for tracking all agent and LLM actions.
This module provides detailed logging of agent activities, LLM calls, and tool usage.
"""

import logging
import json
import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union

from services.supabase import DBConnection
from utils.logger import logger as app_logger

# Set up file logger
agent_logger = logging.getLogger("agent_actions")
agent_logger.setLevel(logging.INFO)

# Create logs directory if it doesn't exist
os.makedirs("/app/logs/agent_actions", exist_ok=True)

# Add file handler
file_handler = logging.FileHandler(f"/app/logs/agent_actions/actions_{datetime.now().strftime('%Y%m%d')}.log")
file_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add handler to logger
agent_logger.addHandler(file_handler)

async def log_agent_action_to_db(
    thread_id: str,
    action_type: str,
    action_details: Dict[str, Any],
    agent_run_id: Optional[str] = None,
    project_id: Optional[str] = None
) -> None:
    """
    Log agent action to the Supabase database.
    
    Args:
        thread_id: The ID of the thread
        action_type: Type of action (e.g., 'tool_call', 'llm_request', 'agent_start')
        action_details: Details about the action
        agent_run_id: Optional ID of the agent run
        project_id: Optional ID of the project
    """
    try:
        # Connect to Supabase
        db = DBConnection()
        client = await db.client
        
        # Insert log entry
        await client.table("agent_action_logs").insert({
            "thread_id": thread_id,
            "agent_run_id": agent_run_id,
            "project_id": project_id,
            "action_type": action_type,
            "action_details": action_details
        }).execute()
        
        app_logger.info(f"Logged agent action to database: {action_type} for thread {thread_id}")
    except Exception as e:
        app_logger.error(f"Failed to log agent action to database: {e}")

def log_agent_action(
    thread_id: str,
    action_type: str,
    action_details: Dict[str, Any],
    agent_run_id: Optional[str] = None,
    project_id: Optional[str] = None
) -> None:
    """
    Log information about an agent action.
    
    Args:
        thread_id: The ID of the thread
        action_type: Type of action (e.g., 'tool_call', 'llm_request', 'agent_start')
        action_details: Details about the action
        agent_run_id: Optional ID of the agent run
        project_id: Optional ID of the project
    """
    # Log to file
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "thread_id": thread_id,
        "agent_run_id": agent_run_id,
        "project_id": project_id,
        "action_type": action_type,
        "action_details": action_details
    }
    
    agent_logger.info(json.dumps(log_data))
    
    # Also log to database asynchronously
    try:
        # Check if we're already in an event loop
        try:
            loop = asyncio.get_running_loop()
            # If we're in an event loop, create a task instead of a new loop
            asyncio.create_task(log_agent_action_to_db(thread_id, action_type, action_details, agent_run_id, project_id))
        except RuntimeError:
            # No running event loop, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(log_agent_action_to_db(thread_id, action_type, action_details, agent_run_id, project_id))
            loop.close()
    except Exception as e:
        app_logger.error(f"Error calling async database logging: {e}")

def log_llm_request(
    thread_id: str,
    model_name: str,
    prompt: str,
    agent_run_id: Optional[str] = None,
    project_id: Optional[str] = None,
    tokens_used: Optional[int] = None,
    duration_ms: Optional[int] = None
) -> None:
    """
    Log an LLM request.
    
    Args:
        thread_id: The ID of the thread
        model_name: Name of the model used
        prompt: The prompt sent to the LLM (truncated for privacy)
        agent_run_id: Optional ID of the agent run
        project_id: Optional ID of the project
        tokens_used: Optional count of tokens used
        duration_ms: Optional duration of the request in milliseconds
    """
    # Truncate prompt for privacy (just log first 100 chars)
    truncated_prompt = prompt[:100] + "..." if len(prompt) > 100 else prompt
    
    action_details = {
        "model_name": model_name,
        "prompt_snippet": truncated_prompt,
        "prompt_length": len(prompt),
        "tokens_used": tokens_used,
        "duration_ms": duration_ms
    }
    
    log_agent_action(thread_id, "llm_request", action_details, agent_run_id, project_id)

def log_tool_usage(
    thread_id: str,
    tool_name: str,
    tool_args: Dict[str, Any],
    tool_result: Optional[Any] = None,
    agent_run_id: Optional[str] = None,
    project_id: Optional[str] = None,
    duration_ms: Optional[int] = None,
    error: Optional[str] = None
) -> None:
    """
    Log a tool usage.
    
    Args:
        thread_id: The ID of the thread
        tool_name: Name of the tool used
        tool_args: Arguments passed to the tool
        tool_result: Optional result from the tool (may be truncated)
        agent_run_id: Optional ID of the agent run
        project_id: Optional ID of the project
        duration_ms: Optional duration of the tool call in milliseconds
        error: Optional error message if the tool call failed
    """
    # Convert tool_result to string and truncate if needed
    if tool_result is not None:
        if isinstance(tool_result, (dict, list)):
            tool_result_str = json.dumps(tool_result)
        else:
            tool_result_str = str(tool_result)
        
        # Truncate result if too long
        if len(tool_result_str) > 500:
            tool_result_str = tool_result_str[:500] + "..."
    else:
        tool_result_str = None
    
    action_details = {
        "tool_name": tool_name,
        "tool_args": tool_args,
        "tool_result": tool_result_str,
        "duration_ms": duration_ms,
        "error": error
    }
    
    log_agent_action(thread_id, "tool_usage", action_details, agent_run_id, project_id)

def log_agent_start(
    thread_id: str,
    agent_run_id: str,
    project_id: str,
    model_name: str,
    enable_thinking: bool,
    reasoning_effort: str,
    enable_context_manager: bool
) -> None:
    """
    Log the start of an agent run.
    
    Args:
        thread_id: The ID of the thread
        agent_run_id: ID of the agent run
        project_id: ID of the project
        model_name: Name of the model used
        enable_thinking: Whether thinking is enabled
        reasoning_effort: Level of reasoning effort
        enable_context_manager: Whether context manager is enabled
    """
    action_details = {
        "model_name": model_name,
        "enable_thinking": enable_thinking,
        "reasoning_effort": reasoning_effort,
        "enable_context_manager": enable_context_manager
    }
    
    log_agent_action(thread_id, "agent_start", action_details, agent_run_id, project_id)

def log_agent_stop(
    thread_id: str,
    agent_run_id: str,
    project_id: str,
    status: str,
    error: Optional[str] = None,
    duration_ms: Optional[int] = None
) -> None:
    """
    Log the stop of an agent run.
    
    Args:
        thread_id: The ID of the thread
        agent_run_id: ID of the agent run
        project_id: ID of the project
        status: Status of the agent run (completed, stopped, failed)
        error: Optional error message if the agent run failed
        duration_ms: Optional duration of the agent run in milliseconds
    """
    action_details = {
        "status": status,
        "error": error,
        "duration_ms": duration_ms
    }
    
    log_agent_action(thread_id, "agent_stop", action_details, agent_run_id, project_id)

def log_file_operation(
    thread_id: str,
    operation_type: str,
    file_path: str,
    content_snippet: Optional[str] = None,
    agent_run_id: Optional[str] = None,
    project_id: Optional[str] = None
) -> None:
    """
    Log a file operation.
    
    Args:
        thread_id: The ID of the thread
        operation_type: Type of operation (read, write, update, delete)
        file_path: Path of the file
        content_snippet: Optional snippet of the file content (for write/update)
        agent_run_id: Optional ID of the agent run
        project_id: Optional ID of the project
    """
    # Truncate content snippet if needed
    if content_snippet and len(content_snippet) > 200:
        content_snippet = content_snippet[:200] + "..."
    
    action_details = {
        "operation_type": operation_type,
        "file_path": file_path,
        "content_snippet": content_snippet
    }
    
    log_agent_action(thread_id, "file_operation", action_details, agent_run_id, project_id)

async def get_agent_action_logs(
    thread_id: Optional[str] = None,
    agent_run_id: Optional[str] = None,
    project_id: Optional[str] = None,
    action_type: Optional[str] = None,
    days: int = 7
) -> List[Dict[str, Any]]:
    """
    Get agent action logs from the database.
    
    Args:
        thread_id: Optional thread ID to filter by
        agent_run_id: Optional agent run ID to filter by
        project_id: Optional project ID to filter by
        action_type: Optional action type to filter by
        days: Number of days to look back
        
    Returns:
        List of agent action logs
    """
    try:
        # Connect to Supabase
        db = DBConnection()
        client = await db.client
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Start building the query
        query = client.table("agent_action_logs")\
            .select("*")\
            .gte("created_at", start_date.isoformat())\
            .lte("created_at", end_date.isoformat())
        
        # Add filters if provided
        if thread_id:
            query = query.eq("thread_id", thread_id)
        if agent_run_id:
            query = query.eq("agent_run_id", agent_run_id)
        if project_id:
            query = query.eq("project_id", project_id)
        if action_type:
            query = query.eq("action_type", action_type)
        
        # Order by created_at
        query = query.order("created_at", desc=True)
        
        # Execute the query
        response = await query.execute()
        
        return response.data or []
    except Exception as e:
        app_logger.error(f"Error getting agent action logs: {e}")
        return []
