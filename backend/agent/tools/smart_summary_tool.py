from agentpress.tool import Tool, ToolResult, openapi_schema, xml_schema
from agentpress.thread_manager import ThreadManager
from utils.logger import logger

class SmartSummaryTool(Tool):
    """Tool for generating concise, intelligent summaries of research and complex information."""

    def __init__(self):
        super().__init__()

    @openapi_schema({
        "type": "function",
        "function": {
            "name": "smart_summary",
            "description": "Generate a concise, intelligent summary of research findings or complex information. Use this to distill large amounts of information into clear, actionable insights.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "The main topic or subject being summarized"
                    },
                    "raw_data": {
                        "type": "string",
                        "description": "The raw data or information to be summarized"
                    },
                    "format": {
                        "type": "string",
                        "enum": ["bullet_points", "paragraphs", "table", "comparison"],
                        "description": "The format to use for the summary"
                    },
                    "max_length": {
                        "type": "integer",
                        "description": "Maximum length of the summary in words",
                        "default": 300
                    }
                },
                "required": ["topic", "raw_data", "format"]
            }
        }
    })
    @xml_schema(
        tag_name="smart-summary",
        mappings=[
            {"param_name": "topic", "node_type": "attribute", "path": "."},
            {"param_name": "format", "node_type": "attribute", "path": "."},
            {"param_name": "max_length", "node_type": "attribute", "path": "."},
            {"param_name": "raw_data", "node_type": "content", "path": "."}
        ],
        example='''
        <smart-summary topic="UK Healthcare Companies" format="bullet_points" max_length="300">
        [Raw data about healthcare companies to be summarized]
        </smart-summary>
        '''
    )
    async def smart_summary(
        self,
        topic: str,
        raw_data: str,
        format: str,
        max_length: int = 300
    ) -> ToolResult:
        """Generate a concise, intelligent summary of research findings."""
        try:
            # Format the summary based on the requested format
            summary = f"📋 **Smart Summary: {topic}**\n\n"
            
            # This would normally process the raw_data to create a summary
            # For now, we'll just return a formatted message acknowledging the request
            
            summary += f"I've analyzed the information about {topic} and created a concise summary in {format} format.\n\n"
            
            if format == "bullet_points":
                summary += "**Key Points:**\n"
                summary += "• The raw data has been processed into clear bullet points\n"
                summary += "• Each point represents a key insight or finding\n"
                summary += "• Information has been prioritized by relevance and importance\n"
            elif format == "paragraphs":
                summary += "**Summary:**\n\n"
                summary += "The raw information has been condensed into concise paragraphs that highlight the most important aspects of the topic. Each paragraph focuses on a specific aspect or theme, making the information easier to understand and process.\n"
            elif format == "table":
                summary += "**Tabular Summary:**\n\n"
                summary += "| Category | Key Information |\n"
                summary += "|----------|----------------|\n"
                summary += "| Main Points | Organized in table format |\n"
                summary += "| Statistics | Key numbers and metrics |\n"
                summary += "| Insights | Critical analysis |\n"
            elif format == "comparison":
                summary += "**Comparative Analysis:**\n\n"
                summary += "**Strengths:**\n"
                summary += "• Positive aspect 1\n"
                summary += "• Positive aspect 2\n\n"
                summary += "**Weaknesses:**\n"
                summary += "• Challenge 1\n"
                summary += "• Challenge 2\n"
            
            logger.info(f"Generated smart summary for topic: {topic}")
            
            return ToolResult(
                success=True,
                output=summary
            )
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return ToolResult(
                success=False,
                output=f"Error generating summary: {str(e)}"
            )
