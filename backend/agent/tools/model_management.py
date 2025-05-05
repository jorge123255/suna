"""
Model management tools for the agent.

This module provides tools for managing LLM models on the Ollama server,
including listing available models, downloading new models, and selecting
a model to use for inference.
"""

import asyncio
from typing import Dict, Any, List, Optional
import json

from services.llm import list_ollama_models, download_ollama_model, select_ollama_model
from utils.logger import logger
from utils.config import config

async def list_models_tool(tool_name: str = None) -> Dict[str, Any]:
    """
    List all available models on the Ollama server.
    
    Returns:
        Dict containing the result of the operation and the list of available models
    """
    try:
        models_data = await list_ollama_models()
        models = models_data.get("models", [])
        
        # Format the model information for better readability
        formatted_models = []
        for model in models:
            formatted_models.append({
                "name": model.get("name"),
                "size": model.get("size"),
                "modified_at": model.get("modified_at"),
                "details": model.get("details", {})
            })
        
        # Highlight the currently selected model
        current_model = config.MODEL_TO_USE
        
        return {
            "success": True,
            "models": formatted_models,
            "current_model": current_model,
            "message": f"Found {len(formatted_models)} models on the Ollama server."
        }
    except Exception as e:
        logger.error(f"Error listing models: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to list models from the Ollama server."
        }

async def download_model_tool(model_name: str, tool_name: str = None) -> Dict[str, Any]:
    """
    Download a model to the Ollama server.
    
    Args:
        model_name: Name of the model to download (e.g., "llama3:8b")
    
    Returns:
        Dict containing the result of the operation
    """
    if not model_name:
        return {
            "success": False,
            "error": "Model name is required",
            "message": "Please provide a valid model name to download."
        }
    
    try:
        # Start the download process
        progress_updates = []
        async for progress in download_ollama_model(model_name):
            # Store progress updates
            progress_updates.append(progress)
            
            # Log progress
            if "status" in progress:
                if "completed" in progress and "total" in progress:
                    percentage = (progress["completed"] / progress["total"]) * 100 if progress["total"] > 0 else 0
                    logger.info(f"Downloading {model_name}: {percentage:.2f}% - {progress['status']}")
                else:
                    logger.info(f"Downloading {model_name}: {progress['status']}")
        
        return {
            "success": True,
            "model_name": model_name,
            "progress": progress_updates,
            "message": f"Successfully downloaded model {model_name}."
        }
    except Exception as e:
        logger.error(f"Error downloading model {model_name}: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to download model {model_name}."
        }

async def select_model_tool(model_name: str, tool_name: str = None) -> Dict[str, Any]:
    """
    Select a model to use for inference.
    
    Args:
        model_name: Name of the model to select
    
    Returns:
        Dict containing the result of the operation
    """
    if not model_name:
        return {
            "success": False,
            "error": "Model name is required",
            "message": "Please provide a valid model name to select."
        }
    
    try:
        # Try to select the model
        success = await select_ollama_model(model_name)
        
        if success:
            return {
                "success": True,
                "model_name": model_name,
                "message": f"Successfully selected model {model_name} for inference."
            }
        else:
            return {
                "success": False,
                "error": f"Model {model_name} not found on the Ollama server",
                "message": f"The model {model_name} could not be selected. Make sure it exists on the Ollama server."
            }
    except Exception as e:
        logger.error(f"Error selecting model {model_name}: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to select model {model_name}."
        }
