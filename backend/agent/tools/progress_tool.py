from agentpress.tool import Tool, ToolResult, openapi_schema, xml_schema
from agentpress.thread_manager import ThreadManager
from utils.logger import logger

class ProgressTool(Tool):
    """Tool for tracking and reporting agent progress to the user."""

    def __init__(self):
        super().__init__()

    @openapi_schema({
        "type": "function",
        "function": {
            "name": "update_progress",
            "description": "Update the user on the current progress of a multi-step task. Use this to provide clear status updates on what has been done and what's coming next.",
            "parameters": {
                "type": "object",
                "properties": {
                    "current_step": {
                        "type": "integer",
                        "description": "The current step number in the process"
                    },
                    "total_steps": {
                        "type": "integer",
                        "description": "The total number of steps in the process"
                    },
                    "step_description": {
                        "type": "string",
                        "description": "A brief description of the current step being performed"
                    },
                    "completed_steps": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List of steps that have been completed so far"
                    },
                    "next_steps": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List of upcoming steps that will be performed next"
                    }
                },
                "required": ["current_step", "total_steps", "step_description"]
            }
        }
    })
    @xml_schema(
        tag_name="update-progress",
        mappings=[
            {"param_name": "current_step", "node_type": "attribute", "path": "."},
            {"param_name": "total_steps", "node_type": "attribute", "path": "."},
            {"param_name": "step_description", "node_type": "element", "path": "step_description"},
            {"param_name": "completed_steps", "node_type": "element", "path": "completed_steps/step"},
            {"param_name": "next_steps", "node_type": "element", "path": "next_steps/step"}
        ],
        example='''
        <update-progress current_step="2" total_steps="5">
            <step_description>Searching for healthcare companies in the UK</step_description>
            <completed_steps>
                <step>Initialized research process</step>
            </completed_steps>
            <next_steps>
                <step>Extract company details from search results</step>
                <step>Compile information into structured format</step>
                <step>Generate PDF report</step>
            </next_steps>
        </update-progress>
        '''
    )
    async def update_progress(
        self,
        current_step: int,
        total_steps: int,
        step_description: str,
        completed_steps: list = None,
        next_steps: list = None
    ) -> ToolResult:
        """Update the user on the current progress of a multi-step task."""
        try:
            # Format the progress message
            progress_percentage = int((current_step / total_steps) * 100)
            
            message = f"📊 **Progress Update: {progress_percentage}% Complete** ({current_step}/{total_steps})\n\n"
            message += f"**Current Step:** {step_description}\n\n"
            
            if completed_steps:
                message += "**Completed:**\n"
                for i, step in enumerate(completed_steps):
                    message += f"✅ {i+1}. {step}\n"
                message += "\n"
            
            if next_steps:
                message += "**Coming Next:**\n"
                for i, step in enumerate(next_steps):
                    message += f"⏳ {i+1}. {step}\n"
            
            logger.info(f"Progress update: {progress_percentage}% - {step_description}")
            
            return ToolResult(
                success=True,
                output=message
            )
        except Exception as e:
            logger.error(f"Error updating progress: {str(e)}")
            return ToolResult(
                success=False,
                output=f"Error updating progress: {str(e)}"
            )
