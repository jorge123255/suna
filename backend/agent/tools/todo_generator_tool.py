"""
Tool for automatically generating and managing todo.md files for the agent.
This ensures the agent always has a structured todo list to work with.
"""

from typing import Optional, Dict, Any
import json

from agentpress.tool import ToolResult, openapi_schema, xml_schema
from agentpress.thread_manager import ThreadManager
from sandbox.sandbox import SandboxToolsBase
from utils.logger import logger
from services.agent_logger import log_file_operation

class TodoGeneratorTool(SandboxToolsBase):
    """Tool for automatically generating and managing todo.md files for the agent."""

    def __init__(self, project_id: str, thread_manager: ThreadManager):
        super().__init__(project_id, thread_manager)
        self.workspace_path = "/workspace"

    @openapi_schema({
        "type": "function",
        "function": {
            "name": "ensure_todo_exists",
            "description": "Ensures that a todo.md file exists for the agent to track tasks. If it doesn't exist, creates it with initial sections.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_description": {
                        "type": "string",
                        "description": "Description of the user's task to include in the todo.md file"
                    },
                    "overwrite": {
                        "type": "boolean",
                        "description": "Whether to overwrite an existing todo.md file",
                        "default": False
                    }
                },
                "required": ["task_description"]
            }
        }
    })
    @xml_schema(
        tag_name="ensure-todo",
        mappings=[
            {"param_name": "task_description", "node_type": "content", "path": "."},
            {"param_name": "overwrite", "node_type": "attribute", "path": "."}
        ],
        example='''
        <ensure-todo overwrite="false">
        Create a React application with a login page
        </ensure-todo>
        '''
    )
    async def ensure_todo_exists(self, task_description: str, overwrite: bool = False) -> ToolResult:
        """
        Ensures that a todo.md file exists for the agent to track tasks.
        If it doesn't exist, creates it with initial sections.
        """
        try:
            # Ensure sandbox is initialized
            await self._ensure_sandbox()
            
            todo_path = f"{self.workspace_path}/todo.md"
            
            # Check if todo.md already exists
            todo_exists = False
            try:
                self.sandbox.fs.get_file_info(todo_path)
                todo_exists = True
            except Exception:
                pass
            
            # If todo.md exists and we're not overwriting, return success
            if todo_exists and not overwrite:
                return self.success_response("todo.md already exists. Use update_todo to modify it.")
            
            # Create initial todo.md content
            todo_content = self._generate_initial_todo(task_description)
            
            # Create or overwrite todo.md
            self.sandbox.fs.upload_file(todo_path, todo_content.encode())
            
            # Log file operation
            thread_id = await self._get_thread_id()
            if thread_id:
                log_file_operation(
                    thread_id=thread_id,
                    operation_type="create" if not todo_exists else "update",
                    file_path="todo.md",
                    content_snippet=todo_content[:200],
                    project_id=self.project_id
                )
            
            action = "created" if not todo_exists else "updated"
            return self.success_response(f"todo.md {action} successfully.")
        except Exception as e:
            return self.fail_response(f"Error ensuring todo.md exists: {str(e)}")

    @openapi_schema({
        "type": "function",
        "function": {
            "name": "update_todo",
            "description": "Updates the todo.md file with completed tasks or new tasks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "completed_tasks": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of tasks that have been completed"
                    },
                    "new_tasks": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of new tasks to add"
                    },
                    "section": {
                        "type": "string",
                        "description": "Section of the todo.md file to update (e.g., 'Initial Research', 'Implementation')",
                        "default": "Tasks"
                    }
                },
                "required": []
            }
        }
    })
    @xml_schema(
        tag_name="update-todo",
        mappings=[
            {"param_name": "completed_tasks", "node_type": "element", "path": "completed_tasks"},
            {"param_name": "new_tasks", "node_type": "element", "path": "new_tasks"},
            {"param_name": "section", "node_type": "attribute", "path": "."}
        ],
        example='''
        <update-todo section="Implementation">
            <completed_tasks>
                ["Set up React project", "Create component structure"]
            </completed_tasks>
            <new_tasks>
                ["Implement login form validation", "Add error handling"]
            </new_tasks>
        </update-todo>
        '''
    )
    async def update_todo(self, completed_tasks: Optional[list] = None, new_tasks: Optional[list] = None, section: str = "Tasks") -> ToolResult:
        """
        Updates the todo.md file with completed tasks or new tasks.
        """
        try:
            # Ensure sandbox is initialized
            await self._ensure_sandbox()
            
            todo_path = f"{self.workspace_path}/todo.md"
            
            # Check if todo.md exists
            try:
                self.sandbox.fs.get_file_info(todo_path)
            except Exception:
                return self.fail_response("todo.md does not exist. Use ensure_todo_exists to create it.")
            
            # Get current todo.md content
            content = self.sandbox.fs.download_file(todo_path).decode()
            
            # Update content with completed tasks and new tasks
            updated_content = self._update_todo_content(content, completed_tasks, new_tasks, section)
            
            # Write updated content back to todo.md
            self.sandbox.fs.upload_file(todo_path, updated_content.encode())
            
            # Log file operation
            thread_id = await self._get_thread_id()
            if thread_id:
                log_file_operation(
                    thread_id=thread_id,
                    operation_type="update",
                    file_path="todo.md",
                    content_snippet=updated_content[:200],
                    project_id=self.project_id
                )
            
            return self.success_response("todo.md updated successfully.")
        except Exception as e:
            return self.fail_response(f"Error updating todo.md: {str(e)}")

    def _generate_initial_todo(self, task_description: str) -> str:
        """
        Generates the initial content for the todo.md file.
        Detects task type and uses appropriate template.
        """
        # Check if this is a market research task
        task_lower = task_description.lower()
        if 'market research' in task_lower or 'market analysis' in task_lower:
            return self._generate_market_research_todo(task_description)
        else:
            return self._generate_default_todo(task_description)
    
    def _generate_market_research_todo(self, task_description: str) -> str:
        """
        Generates a todo list specifically for market research tasks.
        """
        # Extract the industry from the task description if possible
        industry = task_description
        if 'for' in task_description:
            parts = task_description.split('for')
            if len(parts) > 1:
                industry = parts[1].strip()
        
        return f"""# {industry} Market Analysis

## Initial Research
- [ ] Define key {industry} industry segments
- [ ] Research overall {industry} market size and growth trends
- [ ] Identify major players across different segments

## Detailed Analysis
- [ ] Gather detailed information on major players (market share, strengths, weaknesses)
- [ ] Collect website URLs for each major company
- [ ] Analyze market trends and opportunities

## Report Creation
- [ ] Create a structured report outline
- [ ] Write comprehensive market analysis content
- [ ] Format the report with proper styling
- [ ] Generate the final PDF report

## Delivery
- [ ] Review the final report for completeness and accuracy
- [ ] Share the PDF report with the user"""
    
    def _generate_default_todo(self, task_description: str) -> str:
        """
        Generates the default todo list for general tasks.
        """
        return f"""# Task: {task_description}

## Initial Research
- [ ] Understand the requirements
- [ ] Identify key components needed
- [ ] Research best practices and approaches

## Implementation
- [ ] Set up project structure
- [ ] Implement core functionality
- [ ] Add error handling and validation

## Testing
- [ ] Test functionality
- [ ] Fix any bugs
- [ ] Verify requirements are met

## Delivery
- [ ] Clean up code
- [ ] Add documentation
- [ ] Prepare final deliverables
"""

    def _update_todo_content(self, content: str, completed_tasks: Optional[list], new_tasks: Optional[list], section: str) -> str:
        """
        Updates the todo.md content with completed tasks and new tasks.
        """
        lines = content.split('\n')
        section_found = False
        section_index = -1
        
        # Find the section
        for i, line in enumerate(lines):
            if line.strip().startswith(f"## {section}"):
                section_found = True
                section_index = i
                break
        
        # If section not found, add it
        if not section_found:
            lines.append(f"\n## {section}")
            section_index = len(lines) - 1
        
        # Mark completed tasks
        if completed_tasks:
            for i in range(section_index + 1, len(lines)):
                if i >= len(lines) or (lines[i].strip().startswith('#') and lines[i].strip() != '#'):
                    break
                
                for task in completed_tasks:
                    task_text = task.strip()
                    if task_text in lines[i] and "[ ]" in lines[i]:
                        lines[i] = lines[i].replace("[ ]", "[x]")
        
        # Add new tasks
        if new_tasks:
            insert_index = section_index + 1
            # Find the end of the section
            for i in range(section_index + 1, len(lines)):
                if i >= len(lines) or (lines[i].strip().startswith('#') and lines[i].strip() != '#'):
                    insert_index = i
                    break
                insert_index = i + 1
            
            # Insert new tasks
            for task in new_tasks:
                lines.insert(insert_index, f"- [ ] {task.strip()}")
                insert_index += 1
        
        return '\n'.join(lines)

    async def _get_thread_id(self) -> Optional[str]:
        """
        Gets the thread ID for the current project.
        """
        try:
            client = await self.thread_manager.db.client
            project = await client.table('projects').select('thread_id').eq('project_id', self.project_id).execute()
            if project.data and len(project.data) > 0:
                return project.data[0].get('thread_id')
        except Exception as e:
            logger.error(f"Error getting thread ID: {str(e)}")
        return None
