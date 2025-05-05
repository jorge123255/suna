"""
Logger for tracking model selection decisions.
This helps analyze how the automatic model selection is working in real-world usage.
"""

import logging
import json
import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from services.supabase import DBConnection
from utils.logger import logger as app_logger

# Set up file logger
model_logger = logging.getLogger("model_selection")
model_logger.setLevel(logging.INFO)

# Create logs directory if it doesn't exist
os.makedirs("/app/logs/model_selection", exist_ok=True)

# Add file handler
file_handler = logging.FileHandler(f"/app/logs/model_selection/selection_{datetime.now().strftime('%Y%m%d')}.log")
file_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add handler to logger
model_logger.addHandler(file_handler)

async def log_model_selection_to_db(prompt: str, task_type: str, confidence: float, selected_model: str, override_reason: Optional[str] = None) -> None:
    """
    Log model selection information to the Supabase database.
    
    Args:
        prompt: The user's prompt (truncated for privacy)
        task_type: The classified task type
        confidence: The confidence score
        selected_model: The model that was selected
        override_reason: Reason for overriding the classification (if applicable)
    """
    try:
        # Truncate prompt for privacy (just log first 50 chars)
        truncated_prompt = prompt[:50] + "..." if len(prompt) > 50 else prompt
        
        # Connect to Supabase
        db = DBConnection()
        client = await db.client
        
        # Insert log entry
        await client.table("model_selection_logs").insert({
            "prompt_snippet": truncated_prompt,
            "prompt_length": len(prompt),
            "task_type": task_type,
            "confidence": confidence,
            "selected_model": selected_model,
            "override_reason": override_reason
        }).execute()
        
        app_logger.info(f"Logged model selection to database: {selected_model} for {task_type} task")
    except Exception as e:
        app_logger.error(f"Failed to log model selection to database: {e}")

def log_model_selection(prompt: str, task_type: str, confidence: float, selected_model: str, override_reason: Optional[str] = None) -> None:
    """
    Log information about a model selection decision.
    
    Args:
        prompt: The user's prompt (truncated for privacy)
        task_type: The classified task type
        confidence: The confidence score
        selected_model: The model that was selected
        override_reason: Reason for overriding the classification (if applicable)
    """
    # Truncate prompt for privacy (just log first 50 chars)
    truncated_prompt = prompt[:50] + "..." if len(prompt) > 50 else prompt
    
    # Log to file
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "prompt_preview": truncated_prompt,
        "prompt_length": len(prompt),
        "task_type": task_type,
        "confidence": round(confidence, 2),
        "selected_model": selected_model,
        "override_applied": override_reason is not None,
        "override_reason": override_reason
    }
    
    model_logger.info(json.dumps(log_data))
    
    # Also log to database asynchronously
    try:
        # Create a new event loop for the async call
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(log_model_selection_to_db(prompt, task_type, confidence, selected_model, override_reason))
        loop.close()
    except Exception as e:
        app_logger.error(f"Error calling async database logging: {e}")

async def get_selection_stats_from_db(days: int = 7) -> Dict[str, Any]:
    """
    Get model selection statistics from the database for the past N days.
    
    Args:
        days: Number of days to analyze
        
    Returns:
        Dictionary with statistics
    """
    try:
        # Connect to Supabase
        db = DBConnection()
        client = await db.client
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Query the database
        response = await client.table("model_selection_logs")\
            .select("*")\
            .gte("created_at", start_date.isoformat())\
            .lte("created_at", end_date.isoformat())\
            .execute()
        
        logs = response.data
        
        if not logs:
            return {
                "total_selections": 0,
                "models_used": {},
                "task_types": {},
                "confidence_avg": 0,
                "override_rate": 0
            }
        
        # Calculate statistics
        models_used = {}
        task_types = {}
        confidence_sum = 0
        override_count = 0
        
        for log in logs:
            # Count models used
            model = log.get("selected_model")
            models_used[model] = models_used.get(model, 0) + 1
            
            # Count task types
            task = log.get("task_type")
            task_types[task] = task_types.get(task, 0) + 1
            
            # Sum confidence scores
            confidence_sum += log.get("confidence", 0)
            
            # Count overrides
            if log.get("override_reason"):
                override_count += 1
        
        total = len(logs)
        
        return {
            "total_selections": total,
            "models_used": models_used,
            "task_types": task_types,
            "confidence_avg": round(confidence_sum / total, 2) if total > 0 else 0,
            "override_rate": round(override_count / total * 100, 1) if total > 0 else 0
        }
    except Exception as e:
        app_logger.error(f"Error getting model selection stats from database: {e}")
        return {
            "error": str(e),
            "total_selections": 0,
            "models_used": {},
            "task_types": {},
            "confidence_avg": 0,
            "override_rate": 0
        }

def get_selection_stats(days: int = 7) -> Dict[str, Any]:
    """
    Analyze model selection statistics for the past N days.
    
    Args:
        days: Number of days to analyze
        
    Returns:
        Dictionary with statistics
    """
    # Implementation for analyzing logs and generating statistics
    # This would be used for a dashboard or admin view
    stats = {
        "models_used": {},
        "task_types": {},
        "override_count": 0,
        "total_queries": 0,
        "avg_confidence": 0.0
    }
    
    # Future implementation would parse log files and calculate statistics
    
    return stats
