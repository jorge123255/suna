"""
Browser Takeover Tool

This module provides a dedicated tool for requesting user takeover of browser interactions
when automated tools fail or encounter challenges.
"""

from typing import Dict, Any, Optional, List, Union
from agentpress.tool import Tool, ToolResult, openapi_schema, xml_schema
from agentpress.thread_manager import ThreadManager
from utils.logger import logger
import json
import traceback

class BrowserTakeoverTool(Tool):
    """Tool for requesting user takeover of browser interactions."""
    
    def __init__(self, thread_id: str = None, thread_manager: Optional[ThreadManager] = None):
        super().__init__()
        self.thread_id = thread_id
        self.thread_manager = thread_manager
    
    @openapi_schema({
        "type": "function",
        "function": {
            "name": "web_browser_takeover",
            "description": "Request user takeover of browser interaction when automated tools cannot handle the task. Use this when encountering CAPTCHAs, complex interactions, or when automated browsing fails. Provide clear instructions for what the user should do.",
            "parameters": {
                "type": "object",
                "properties": {
                    "instructions": {
                        "type": "string",
                        "description": "Clear, step-by-step instructions for what the user should do in the browser. Be specific about the actions needed and what information to gather."
                    },
                    "url": {
                        "type": "string",
                        "description": "Optional URL the user should navigate to. If provided, this will be suggested to the user as a starting point.",
                        "default": ""
                    },
                    "reason": {
                        "type": "string",
                        "description": "Brief explanation of why automated tools failed and user intervention is needed.",
                        "default": "Automated tools encountered a challenge that requires human assistance."
                    }
                },
                "required": ["instructions"]
            }
        }
    })
    @xml_schema(
        tag_name="web-browser-takeover",
        mappings=[
            {"param_name": "instructions", "node_type": "content", "path": "."},
            {"param_name": "url", "node_type": "attribute", "path": ".", "required": False},
            {"param_name": "reason", "node_type": "attribute", "path": ".", "required": False}
        ],
        example='''
        <!-- Use web-browser-takeover when automated tools cannot handle the task -->
        
        <web-browser-takeover url="https://weather.gov" reason="Weather data requires human verification">
        I need your help to get the current weather for Chicago. Please:
        
        1. Navigate to the National Weather Service website
        2. Enter "Chicago, IL" in the search box
        3. Look for the current temperature and conditions
        4. Let me know what you find
        
        This will help me provide you with accurate weather information.
        </web-browser-takeover>
        '''
    )
    async def web_browser_takeover(self, instructions: str, url: str = "", reason: str = "Automated tools encountered a challenge that requires human assistance.") -> ToolResult:
        """
        Request user takeover of browser interaction.
        
        Args:
            instructions: Clear instructions for what the user should do
            url: Optional URL the user should navigate to
            reason: Explanation of why user intervention is needed
            
        Returns:
            ToolResult indicating the takeover request was sent
        """
        try:
            logger.info(f"Requesting browser takeover. Reason: {reason}")
            
            # Create a message for the user
            takeover_message = {
                "type": "browser_takeover_request",
                "instructions": instructions,
                "url": url,
                "reason": reason,
                "status": "awaiting_user_action"
            }
            
            # If we have a thread manager, add the message to the thread
            if self.thread_manager and self.thread_id:
                await self.thread_manager.add_message(
                    thread_id=self.thread_id,
                    type="browser_takeover",
                    content=json.dumps(takeover_message),
                    is_llm_message=False
                )
            
            return self.success_response({
                "status": "Awaiting user browser takeover",
                "message": "Browser takeover request sent to user",
                "instructions_provided": instructions,
                "url_suggested": url or "None provided"
            })
            
        except Exception as e:
            logger.error(f"Error requesting browser takeover: {str(e)}")
            logger.debug(traceback.format_exc())
            return self.fail_response(f"Error requesting browser takeover: {str(e)}")


# Register this tool with the agent
def register_browser_takeover_tool(thread_manager, thread_id):
    """Register the browser takeover tool with the agent."""
    try:
        thread_manager.add_tool(
            BrowserTakeoverTool,
            thread_id=thread_id,
            thread_manager=thread_manager
        )
        logger.info("Browser takeover tool registered successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to register browser takeover tool: {str(e)}")
        return False
