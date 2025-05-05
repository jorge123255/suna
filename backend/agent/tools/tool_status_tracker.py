from agentpress.tool import Tool, ToolResult, openapi_schema, xml_schema
from utils.logger import logger
import json
import time
from typing import Dict, List, Optional, Any
import re

class ToolStatusTracker(Tool):
    """Tool for tracking and displaying the status of tool executions to the user."""

    def __init__(self):
        super().__init__()
        self.tool_history = {}
        self.execution_counts = {}
        self.reasoning_issues = []
        self.max_issue_history = 10

    @openapi_schema({
        "type": "function",
        "function": {
            "name": "tool_status",
            "description": "Display the status of a tool execution to the user. This helps users understand what the agent is doing in real-time.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["started", "completed", "failed"],
                        "description": "The status of the tool execution"
                    },
                    "tool_name": {
                        "type": "string",
                        "description": "The name of the tool being executed"
                    },
                    "details": {
                        "type": "string",
                        "description": "Additional details about the tool execution"
                    }
                },
                "required": ["status", "tool_name"]
            }
        }
    })
    @xml_schema(
        tag_name="tool-status",
        mappings=[
            {"param_name": "status", "node_type": "attribute", "path": "."},
            {"param_name": "tool_name", "node_type": "attribute", "path": "."},
            {"param_name": "details", "node_type": "content", "path": "."}
        ],
        example='''
        <tool-status status="started" tool_name="web-search">
        Searching for information about UK healthcare companies
        </tool-status>
        '''
    )
    async def tool_status(
        self,
        status: str,
        tool_name: str,
        details: str = ""
    ) -> ToolResult:
        """Display the status of a tool execution to the user."""
        try:
            # Format the status message based on the status type
            if status == "started":
                emoji = "⏳"
                message = f"{emoji} **TOOL STARTING: {tool_name}**\n"
                if details:
                    message += f"_{details}_\n"
                message += "---"
            elif status == "completed":
                emoji = "✅"
                message = f"{emoji} **TOOL COMPLETED: {tool_name}**\n"
                if details:
                    message += f"_{details}_\n"
                message += "---"
            elif status == "failed":
                emoji = "❌"
                message = f"{emoji} **TOOL FAILED: {tool_name}**\n"
                if details:
                    message += f"_{details}_\n"
                message += "---"
            else:
                message = f"**TOOL STATUS [{status}]: {tool_name}**\n"
                if details:
                    message += f"_{details}_\n"
                message += "---"
            
            logger.info(f"Tool status: {status} - {tool_name} - {details}")
            
            return ToolResult(
                success=True,
                output=message
            )
        except Exception as e:
            logger.error(f"Error updating tool status: {str(e)}")
            return ToolResult(
                success=False,
                output=f"Error updating tool status: {str(e)}"
            )

    @openapi_schema({
        "type": "function",
        "function": {
            "name": "log_tool_status",
            "description": "Log the status of a tool execution for tracking purposes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tool_name": {
                        "type": "string",
                        "description": "The name of the tool being logged"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["starting", "completed", "failed"],
                        "description": "The status of the tool execution"
                    },
                    "details": {
                        "type": "string",
                        "description": "Optional details about the tool execution"
                    }
                },
                "required": ["tool_name", "status"]
            }
        }
    })
    async def log_tool_status(self, tool_name: str, status: str, details: Optional[str] = None) -> ToolResult:
        """
        Log the status of a tool execution for tracking purposes.
        """
        try:
            # Update tool_history
            timestamp = time.time()
            if tool_name not in self.tool_history:
                self.tool_history[tool_name] = []
            
            self.tool_history[tool_name].append({
                "status": status,
                "timestamp": timestamp,
                "details": details
            })
            
            # Update execution counts
            if status == "starting":
                if tool_name not in self.execution_counts:
                    self.execution_counts[tool_name] = 0
                self.execution_counts[tool_name] += 1

            # If this is a web search completion, check if reasoning analysis is needed
            if tool_name == "web_search" and status == "completed" and details:
                self._analyze_web_search_response(details)
            
            return self.success_response(f"Tool status logged: {tool_name} - {status}")
        except Exception as e:
            return self.fail_response(f"Error logging tool status: {str(e)}")
    
    @openapi_schema({
        "type": "function",
        "function": {
            "name": "get_tool_stats",
            "description": "Get statistics about tool executions.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    })
    async def get_tool_stats(self) -> ToolResult:
        """
        Get statistics about tool executions.
        """
        try:
            stats = {
                "execution_counts": self.execution_counts,
                "reasoning_issues": self.reasoning_issues
            }
            
            return self.success_response(f"Tool statistics retrieved successfully", stats)
        except Exception as e:
            return self.fail_response(f"Error getting tool statistics: {str(e)}")
            
    @openapi_schema({
        "type": "function",
        "function": {
            "name": "check_reasoning_quality",
            "description": "Check if there are any reasoning quality issues with recent tool executions.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    })
    async def check_reasoning_quality(self) -> ToolResult:
        """
        Check if there are any reasoning quality issues with recent tool executions.
        """
        try:
            if not self.reasoning_issues:
                return self.success_response("No reasoning quality issues detected.", {
                    "has_issues": False,
                    "issues": []
                })
            
            return self.success_response("Reasoning quality issues detected.", {
                "has_issues": True,
                "issues": self.reasoning_issues
            })
        except Exception as e:
            return self.fail_response(f"Error checking reasoning quality: {str(e)}")
            
    def _analyze_web_search_response(self, details: str) -> None:
        """
        Analyze a web search response to check for reasoning quality issues.
        
        This checks if the agent is just returning web search results without
        providing proper analysis or direct answers.
        """
        # Check for signs that the response is just a list of search results
        search_result_patterns = [
            r"here are some (websites|results|links|resources)",
            r"i found (several|some|a few) (websites|results|links|resources)",
            r"you can find information at",
            r"here's what i found"
        ]
        
        weather_query_patterns = [
            r"weather in \w+",
            r"\w+ weather",
            r"temperature in \w+"
        ]
        
        is_likely_search_results = False
        for pattern in search_result_patterns:
            if re.search(pattern, details.lower()):
                is_likely_search_results = True
                break
                
        is_weather_query = False
        for pattern in weather_query_patterns:
            if re.search(pattern, details.lower()):
                is_weather_query = True
                break
                
        # If it's a weather query that's returning just search results, flag it
        if is_weather_query and is_likely_search_results:
            issue = {
                "type": "weather_query_no_synthesis",
                "tool": "web_search",
                "description": "Weather query returned links instead of actual weather data",
                "timestamp": time.time()
            }
            
            self.reasoning_issues.append(issue)
            
            # Keep only the most recent issues
            if len(self.reasoning_issues) > self.max_issue_history:
                self.reasoning_issues = self.reasoning_issues[-self.max_issue_history:]
                
        # Check for other cases where search results are returned without processing
        elif is_likely_search_results and not any(term in details.lower() for term in ["according to", "based on", "i found that", "the information shows"]):
            issue = {
                "type": "search_results_no_synthesis",
                "tool": "web_search",
                "description": "Search results returned without synthesis or analysis",
                "timestamp": time.time()
            }
            
            self.reasoning_issues.append(issue)
            
            # Keep only the most recent issues
            if len(self.reasoning_issues) > self.max_issue_history:
                self.reasoning_issues = self.reasoning_issues[-self.max_issue_history:]
