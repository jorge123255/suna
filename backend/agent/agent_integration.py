"""
Agent Integration Module

This module provides utilities for integrating agent guides and examples 
into the system prompts and agent tools.
"""

import os
import json
import traceback
from typing import Dict, Any, Optional
import logging
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

def get_guide_paths() -> Dict[str, str]:
    """
    Get the paths to all available agent guides.
    """
    # Determine the base directory for guides
    # First check if guides are in the project root
    project_root = Path(__file__).parent.parent.parent
    guides_in_root = list(project_root.glob("agent_*.md"))
    
    if guides_in_root:
        base_dir = project_root
    else:
        # Check if guides are in a docs directory
        docs_dir = project_root / "docs"
        if docs_dir.exists():
            base_dir = docs_dir
        else:
            # Default to the current directory
            base_dir = Path(__file__).parent
    
    # Look for guide files
    guide_files = {
        "prompt_guide": str(base_dir / "agent_prompt_guide.md"),
        "tool_examples": str(base_dir / "agent_tool_examples.md"),
        "workflow_example": str(base_dir / "agent_workflow_example.md"),
        "reasoning_guide": str(base_dir / "agent_reasoning_guide.md"),
        "integration_guide": str(base_dir / "agent_integration_guide.md")
    }
    
    # Filter to only include existing files
    existing_guides = {k: v for k, v in guide_files.items() if os.path.exists(v)}
    
    if not existing_guides:
        logger.warning("No agent guide files found in %s", base_dir)
    else:
        logger.info("Found %d agent guide files in %s", len(existing_guides), base_dir)
        
    return existing_guides

def load_guide_content(guide_type: str) -> Optional[str]:
    """
    Load the content of a specific guide.
    
    Args:
        guide_type: Type of guide to load (prompt_guide, tool_examples, etc.)
        
    Returns:
        The content of the guide, or None if not found
    """
    guide_paths = get_guide_paths()
    
    if guide_type not in guide_paths:
        logger.warning("Guide type '%s' not found", guide_type)
        return None
        
    try:
        with open(guide_paths[guide_type], "r") as f:
            content = f.read()
        return content
    except Exception as e:
        logger.error("Error loading guide '%s': %s", guide_type, str(e))
        return None

def extract_examples_from_guide(guide_content: str, tool_name: str) -> Optional[str]:
    """
    Extract examples for a specific tool from a guide document.
    
    Args:
        guide_content: Content of the guide
        tool_name: Name of the tool to extract examples for
        
    Returns:
        Examples for the tool, or None if not found
    """
    if not guide_content:
        return None
        
    # Look for tool examples section
    tool_sections = {
        "todo": ["## Todo Management Tools", "### Creating a Todo List", "### Updating a Todo List"],
        "files": ["## File Management Tools", "### Creating a File", "### Editing Part of a File"],
        "browser": ["## Browser Tools", "### Navigating to a Website", "### Going Back"],
        "web_search": ["## Web Search Tools", "### Performing a Web Search"]
    }
    
    section_headers = tool_sections.get(tool_name.lower())
    if not section_headers:
        return None
        
    examples = []
    in_section = False
    
    for line in guide_content.split("\n"):
        # Check if we've found a section header
        if any(header in line for header in section_headers):
            in_section = True
            examples.append(line)
            continue
            
        # Check if we've reached the end of the section
        if in_section and line.startswith("## ") and not any(header in line for header in section_headers):
            in_section = False
            break
            
        # Add the line if we're in the section
        if in_section:
            examples.append(line)
            
    return "\n".join(examples) if examples else None

def extract_guidelines_from_reasoning_guide() -> Optional[str]:
    """
    Extract general reasoning guidelines from the reasoning guide.
    
    Returns:
        General reasoning guidelines, or None if not found
    """
    guide_content = load_guide_content("reasoning_guide")
    if not guide_content:
        return None
        
    # Look for the key principles section
    principles_section = "## Key Principles"
    examples_section = "## Practical Examples"
    
    principles = []
    in_section = False
    
    for line in guide_content.split("\n"):
        if principles_section in line:
            in_section = True
            principles.append(line)
            continue
            
        if in_section and examples_section in line:
            break
            
        if in_section:
            principles.append(line)
            
    return "\n".join(principles) if principles else None

def get_todo_tool_guidelines() -> str:
    """
    Get the guidelines for using TodoList tools.
    
    Returns:
        Guidelines for using TodoList tools
    """
    # Try to load from prompt guide
    guide_content = load_guide_content("prompt_guide")
    if not guide_content:
        # Fallback to hardcoded guidelines
        return """
## TodoList Tool Guidelines

1. Always create a todo list first using the ensure-todo tool
2. Use the correct XML format:
   - <ensure-todo overwrite="true|false">Task description</ensure-todo>
   - <update-todo section="Section Name">
       <completed_tasks>
           ["Task 1", "Task 2"]
       </completed_tasks>
       <new_tasks>
           ["New Task 1", "New Task 2"]
       </new_tasks>
     </update-todo>
3. Update the todo list as you complete tasks
4. Add new tasks when you discover additional work needed
"""
    
    # Extract the section about TodoList tools
    todo_section = extract_examples_from_guide(guide_content, "todo")
    return todo_section or "Use TodoList tools to track task progress."

def integrate_reasoning_guidelines(system_prompt: str) -> str:
    """
    Integrate reasoning guidelines into the system prompt.
    
    Args:
        system_prompt: Current system prompt
        
    Returns:
        Updated system prompt with reasoning guidelines
    """
    try:
        # Get reasoning guidelines
        guidelines = extract_guidelines_from_reasoning_guide()
        
        # Add specific fixes for web search and browser takeover
        web_search_fix = """
## WEB SEARCH AND BROWSER INTERACTION GUIDELINES
- When using web_search, always follow through to get the actual information
- If web_search fails or returns only links, use these fallback strategies:
  * Try a more specific search query
  * Use browser_navigate_to to visit one of the relevant websites directly
  * Use scrape_webpage to extract specific data from websites
- For browser-takeover requests:
  * Use the web-browser-takeover tool from MessageTool when automated tools fail
  * Provide clear, step-by-step instructions for the user
  * Explain exactly what you're trying to accomplish
- For weather requests specifically:
  1. Search for the location's weather using web_search
  2. If that fails, navigate directly to weather.gov or accuweather.com
  3. Extract the current temperature, conditions, and forecast
  4. Present the information clearly to the user
"""
        
        # Combine guidelines
        if not guidelines:
            logger.warning("No reasoning guidelines found, using web search fix only")
            combined_guidelines = web_search_fix
        else:
            combined_guidelines = guidelines + "\n\n" + web_search_fix
        
        # Integrate guidelines into the prompt
        # Look for the EXECUTION APPROACH section to insert our guidelines
        if "## EXECUTION APPROACH" in system_prompt:
            # Insert before the execution approach section
            parts = system_prompt.split("## EXECUTION APPROACH")
            enhanced_prompt = parts[0] + combined_guidelines + "\n\n## EXECUTION APPROACH" + parts[1]
        else:
            # Just append to the end if section not found
            enhanced_prompt = system_prompt + "\n\n" + combined_guidelines
        
        logger.info("Successfully integrated reasoning guidelines and web search fixes into system prompt")
        return enhanced_prompt
    except Exception as e:
        logger.error(f"Error integrating reasoning guidelines: {str(e)}")
        return system_prompt

def register_agent_monitors(agent):
    """
    Register monitoring hooks with the agent.
    
    Args:
        agent: The agent instance to register monitors with
    """
    # This would be implemented based on the agent framework
    # For example, we might register hooks to check reasoning quality
    # after each agent response
    pass

def register_agent_tools(agent, thread_id, thread_manager):
    """
    Register tools with the agent.
    
    Args:
        agent: The agent to register tools with
        thread_id: The thread ID for the agent
        thread_manager: The thread manager for the agent
    """
    try:
        # Import the tools
        from agent.tools.browser_takeover import BrowserTakeoverTool
        from agent.tools.market_research_tool import MarketResearchTool
        from agent.tools.todo_generator_tool import TodoGeneratorTool
        
        # Register tools with the agent
        logger.info("Registering tools with agent")
        
        # Register the todo generator tool FIRST to ensure it's prioritized
        todo_tool = agent.register_tool(
            TodoGeneratorTool,
            project_id=agent.project_id,
            thread_manager=thread_manager
        )
        
        # Register the market research tool
        market_tool = agent.register_tool(
            MarketResearchTool,
            thread_id=thread_id,
            thread_manager=thread_manager,
            project_id=agent.project_id
        )
        
        # Register the browser takeover tool
        agent.register_tool(
            BrowserTakeoverTool,
            thread_id=thread_id,
            thread_manager=thread_manager
        )
        
        # Add a hook to automatically create a todo at the start of a task
        def on_task_start(task_description):
            # Get the first message which should contain the task description
            if task_description and isinstance(task_description, str):
                logger.info(f"Automatically creating todo for task: {task_description[:50]}...")
                # Use the todo generator tool to create a todo
                return todo_tool.ensure_todo_exists(task_description=task_description, overwrite=True)
            return None
        
        # Register the hook with the agent
        if hasattr(agent, 'register_task_start_hook'):
            agent.register_task_start_hook(on_task_start)
            logger.info("Registered task start hook for todo generation")
        
        logger.info("Successfully registered tools with agent")
        
        return True
    except Exception as e:
        logger.error(f"Error registering agent tools: {str(e)}")
        return False

# Main function to apply all integration changes
def apply_integration(agent=None, thread_id=None, thread_manager=None):
    """
    Apply all integration changes.
    
    Args:
        agent: Optional agent to apply integrations to
        thread_id: Optional thread ID for the agent
        thread_manager: Optional thread manager for the agent
        
    Returns:
        Boolean indicating success or failure
    """
    try:
        logger.info("Applying all agent integration enhancements")
        
        # Step 1: Update the system prompt with reasoning guidelines
        if hasattr(agent, 'system_prompt'):
            agent.system_prompt = integrate_reasoning_guidelines(agent.system_prompt)
            logger.info("Successfully integrated reasoning guidelines into system prompt")
        
        # Step 2: Register enhanced tools with the agent
        if agent and thread_id and thread_manager:
            success = register_agent_tools(agent, thread_id, thread_manager)
            if not success:
                logger.warning("Failed to register some agent tools")
        
        # Step 3: Register agent monitors if needed
        if agent:
            register_agent_monitors(agent)
        
        logger.info("Successfully applied all agent integration enhancements")
        return True
    except Exception as e:
        logger.error(f"Error applying integration changes: {str(e)}")
        traceback.print_exc()
        return False