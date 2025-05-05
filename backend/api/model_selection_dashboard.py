"""
API endpoints for the model selection dashboard.
This allows monitoring how the automatic model selection is working with real users.
"""

from fastapi import APIRouter, Depends, HTTPException
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from services.model_selection_logger import get_selection_stats, get_selection_stats_from_db
from services.supabase import DBConnection
from utils.logger import logger

router = APIRouter(prefix="/api/model-selection", tags=["model_selection"])

@router.get("/stats")
async def get_model_selection_stats(days: int = 7):
    """
    Get statistics about model selection for the past N days.
    
    Args:
        days: Number of days to analyze
    """
    try:
        # Get stats from the database
        db_stats = await get_selection_stats_from_db(days)
        
        # If there's no database data, try to get stats from log files as fallback
        if db_stats.get("total_selections", 0) == 0:
            logger.info("No database stats available, falling back to log files")
            file_stats = get_selection_stats(days)
            return {
                "source": "log_files",
                "stats": file_stats,
                "message": "Using log files as fallback (database has no data)"
            }
        
        return {
            "source": "database",
            "stats": db_stats
        }
    except Exception as e:
        logger.error(f"Error getting model selection stats: {e}")
        return {"error": str(e)}

@router.get("/recent")
async def get_recent_selections(limit: int = 50):
    """
    Get the most recent model selections from the database.
    
    Args:
        limit: Maximum number of entries to return
    """
    try:
        # Connect to Supabase
        db = DBConnection()
        client = await db.client
        
        # Query the database for recent selections
        response = await client.table("model_selection_logs")\
            .select("*")\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        
        logs = response.data
        
        if not logs:
            # If no database data, try to get from log files as fallback
            logger.info("No database records for recent selections, checking log files")
            
            # Check if log directory exists
            log_dir = "/app/logs/model_selection"
            if not os.path.exists(log_dir):
                return {"message": "No log data available yet", "selections": []}
            
            # Get the most recent log file
            log_files = []
            current_date = datetime.now().strftime('%Y%m%d')
            file_path = f"{log_dir}/selection_{current_date}.log"
            if os.path.exists(file_path):
                log_files.append(file_path)
            
            if not log_files:
                return {"message": "No log data for today", "selections": []}
            
            # Parse log file and get recent entries
            recent_entries = []
            with open(log_files[0], 'r') as f:
                for line in f:
                    try:
                        # Extract the JSON part of the log entry
                        parts = line.split(' - INFO - ')
                        if len(parts) < 2:
                            continue
                        
                        json_str = parts[1].strip()
                        entry = json.loads(json_str)
                        
                        # Add timestamp from log line
                        timestamp = parts[0].strip()
                        entry["log_timestamp"] = timestamp
                        
                        recent_entries.append(entry)
                    except Exception as e:
                        logger.error(f"Error parsing log line: {e}")
                        continue
            
            # Sort by timestamp (newest first) and limit
            recent_entries.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            recent_entries = recent_entries[:limit]
            
            return {
                "source": "log_files",
                "message": "Using log files as fallback (database has no data)",
                "selections": recent_entries
            }
        
        # Format database results
        selections = []
        for log in logs:
            selections.append({
                "id": log.get("id"),
                "timestamp": log.get("created_at"),
                "prompt_preview": log.get("prompt_snippet"),
                "prompt_length": log.get("prompt_length"),
                "task_type": log.get("task_type"),
                "confidence": log.get("confidence"),
                "selected_model": log.get("selected_model"),
                "override_reason": log.get("override_reason")
            })
        
        return {
            "source": "database",
            "selections": selections
        }
    except Exception as e:
        logger.error(f"Error getting recent model selections: {e}")
        return {"error": str(e)}
