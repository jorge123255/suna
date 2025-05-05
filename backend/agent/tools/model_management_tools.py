from typing import Dict, Any, List, Optional
import asyncio
from agentpress.tool import Tool, SchemaType, ToolSchema
from agent.tools.model_management import list_models_tool, download_model_tool, select_model_tool
from utils.logger import logger

class ListModelsToolWrapper(Tool):
    """Tool for listing available models on the Ollama server."""
    
    def get_schemas(self) -> Dict[str, List[ToolSchema]]:
        """Get the schemas for the tool."""
        return {
            "list_models": [
                ToolSchema(
                    schema_type=SchemaType.OPENAPI,
                    schema={
                        "type": "function",
                        "function": {
                            "name": "list_models",
                            "description": "List all available models on the Ollama server",
                            "parameters": {
                                "type": "object",
                                "properties": {},
                                "required": []
                            }
                        }
                    }
                )
            ]
        }
    
    async def list_models(self) -> Dict[str, Any]:
        """List all available models on the Ollama server."""
        try:
            result = await list_models_tool(tool_name="list-models")
            return result
        except Exception as e:
            logger.error(f"Error listing models: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to list models: {str(e)}"
            }


class DownloadModelToolWrapper(Tool):
    """Tool for downloading models to the Ollama server."""
    
    def get_schemas(self) -> Dict[str, List[ToolSchema]]:
        """Get the schemas for the tool."""
        return {
            "download_model": [
                ToolSchema(
                    schema_type=SchemaType.OPENAPI,
                    schema={
                        "type": "function",
                        "function": {
                            "name": "download_model",
                            "description": "Download a model to the Ollama server",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "model_name": {
                                        "type": "string",
                                        "description": "Name of the model to download"
                                    }
                                },
                                "required": ["model_name"]
                            }
                        }
                    }
                )
            ]
        }
    
    async def download_model(self, model_name: str) -> Dict[str, Any]:
        """Download a model to the Ollama server."""
        try:
            result = await download_model_tool(model_name=model_name, tool_name="download-model")
            return result
        except Exception as e:
            logger.error(f"Error downloading model {model_name}: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to download model {model_name}: {str(e)}"
            }


class SelectModelToolWrapper(Tool):
    """Tool for selecting a model to use for inference."""
    
    def get_schemas(self) -> Dict[str, List[ToolSchema]]:
        """Get the schemas for the tool."""
        return {
            "select_model": [
                ToolSchema(
                    schema_type=SchemaType.OPENAPI,
                    schema={
                        "type": "function",
                        "function": {
                            "name": "select_model",
                            "description": "Select a model to use for inference",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "model_name": {
                                        "type": "string",
                                        "description": "Name of the model to select"
                                    }
                                },
                                "required": ["model_name"]
                            }
                        }
                    }
                )
            ]
        }
    
    async def select_model(self, model_name: str) -> Dict[str, Any]:
        """Select a model to use for inference."""
        try:
            result = await select_model_tool(model_name=model_name, tool_name="select-model")
            return result
        except Exception as e:
            logger.error(f"Error selecting model {model_name}: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to select model {model_name}: {str(e)}"
            }
