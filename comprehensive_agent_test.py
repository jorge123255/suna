#!/usr/bin/env python3
"""
Comprehensive Agent Test

This script performs a detailed test of all agent tools with comprehensive logging
to identify why tools (especially TodoGeneratorTool) might not be working correctly.
It focuses on tool registration, invocation patterns, and error logging.
"""

import os
import sys
import json
import asyncio
import time
import uuid
import logging
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from traceback import format_exc
from unittest.mock import MagicMock, patch

# Add the backend directory to the path so we can import from it
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"test_output/agent_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)

logger = logging.getLogger("comprehensive_agent_test")
logger.setLevel(logging.DEBUG)

# Ensure test_output directory exists
os.makedirs("test_output", exist_ok=True)

class ToolCallMonitor:
    """Detailed monitor for tool calls made by the agent"""
    
    def __init__(self):
        self.tool_calls = []
        self.first_tool = None
        self.tool_call_counts = {}
        self.tool_call_errors = {}
        self.original_tools = set()
        self.registered_tools = set()
        self.expected_tools = {
            'ensure_todo_exists',  # TodoGeneratorTool
            'update_todo',         # TodoGeneratorTool
            'execute_command',     # SandboxShellTool
            'create_file',         # SandboxFilesTool
            'str_replace',         # SandboxFilesTool
            'full_file_rewrite',   # SandboxFilesTool
            'delete_file',         # SandboxFilesTool
            'browser_navigate_to', # SandboxBrowserTool
            'browser_go_back',     # SandboxBrowserTool
            'browser_click_element', # SandboxBrowserTool
            'browser_input_text',  # SandboxBrowserTool
            'browser_send_keys',   # SandboxBrowserTool
            'web_search',          # WebSearchTool
            'scrape_webpage'       # SandboxBrowserTool
        }
        
    def record_original_tools(self, tools: Set[str]):
        """Record the original tools available in the system"""
        self.original_tools = tools
        logger.info(f"Original tools available: {sorted(tools)}")
        
    def record_registered_tools(self, tools: Set[str]):
        """Record the tools that were registered with the agent"""
        self.registered_tools = tools
        logger.info(f"Registered tools: {sorted(tools)}")
        
        # Check if expected tools are registered
        missing_tools = self.expected_tools - self.registered_tools
        if missing_tools:
            logger.error(f"Missing expected tools: {sorted(missing_tools)}")
        else:
            logger.info("All expected tools are registered")
    
    def add_tool_call(self, tool_name: str, tool_args: Dict[str, Any], successful: bool = True, error=None):
        """Record a tool call with details and error tracking"""
        self.tool_calls.append({
            "tool_name": tool_name,
            "args": tool_args,
            "timestamp": time.time(),
            "successful": successful,
            "error": str(error) if error else None
        })
        
        # Record the first tool call
        if not self.first_tool:
            self.first_tool = tool_name
            
        # Update tool call counts
        self.tool_call_counts[tool_name] = self.tool_call_counts.get(tool_name, 0) + 1
        
        # Track errors by tool
        if not successful and error:
            if tool_name not in self.tool_call_errors:
                self.tool_call_errors[tool_name] = []
            self.tool_call_errors[tool_name].append(str(error))
            
    def get_first_tool(self) -> Optional[str]:
        """Get the name of the first tool called"""
        return self.first_tool
    
    def print_summary(self):
        """Print a comprehensive summary of all tool activity"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TOOL CALL SUMMARY")
        print("=" * 80)
        
        # Tool registration summary
        print("\n🔧 Tool Registration:")
        print(f"Original tools: {len(self.original_tools)}")
        print(f"Registered tools: {len(self.registered_tools)}")
        
        missing_tools = self.expected_tools - self.registered_tools
        if missing_tools:
            print(f"❌ Missing expected tools: {sorted(missing_tools)}")
        else:
            print("✅ All expected tools are registered")
        
        # Tool call statistics
        print("\n📈 Tool Call Statistics:")
        if not self.tool_calls:
            print("No tool calls recorded")
        else:
            print(f"Total tool calls: {len(self.tool_calls)}")
            print(f"First tool called: {self.first_tool}")
            print("\nCall counts by tool:")
            for tool, count in sorted(self.tool_call_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"  - {tool}: {count} calls")
        
        # Error summary
        print("\n❌ Tool Call Errors:")
        if not self.tool_call_errors:
            print("No errors recorded")
        else:
            print(f"Tools with errors: {len(self.tool_call_errors)}")
            for tool, errors in self.tool_call_errors.items():
                print(f"\n  Tool: {tool}")
                print(f"  Error count: {len(errors)}")
                print("  Sample errors:")
                for i, error in enumerate(errors[:3]):  # Show at most 3 sample errors
                    print(f"    {i+1}. {error[:150]}...")
                if len(errors) > 3:
                    print(f"    ... and {len(errors) - 3} more errors")
        
        # Tool call timeline
        print("\n⏱️ Tool Call Timeline:")
        if not self.tool_calls:
            print("No tool calls recorded")
        else:
            start_time = self.tool_calls[0]["timestamp"]
            for i, call in enumerate(self.tool_calls):
                relative_time = call["timestamp"] - start_time
                status = "✅" if call["successful"] else "❌"
                print(f"{status} {relative_time:.2f}s - {call['tool_name']}")
                if i < 5 or i >= len(self.tool_calls) - 5:  # Show first and last 5 calls
                    print(f"     Args: {json.dumps(call['args'], indent=2)[:150]}")
                    if not call["successful"]:
                        print(f"     Error: {call['error']}")
                elif i == 5:
                    print(f"     ... {len(self.tool_calls) - 10} more calls ...")

async def setup_test_environment():
    """Set up the test environment with all necessary database entries"""
    from services.supabase import DBConnection
    
    # Initialize the database connection
    client = await DBConnection().client
    
    print("\n🔍 Setting up test environment...")
    
    # Create test IDs
    account_id = str(uuid.uuid4())
    project_id = str(uuid.uuid4())
    thread_id = str(uuid.uuid4())
    sandbox_id = f"test-sandbox-{uuid.uuid4().hex[:8]}"
    
    try:
        # Try to create the project directly
        project_name = f"comprehensive_test_{uuid.uuid4().hex[:8]}"
        
        # Create project directly
        project_result = await client.from_('projects').insert({
            "project_id": project_id,
            "name": project_name,
            "account_id": account_id,
            "sandbox": {
                "id": sandbox_id,
                "status": "running",
                "pass": "test-password"
            }
        }).execute()
        
        if not project_result.error:
            print(f"✅ Created test project: {project_id} ({project_name})")
            
            # Create a test thread
            print("Creating test thread...")
            
            thread_result = await client.from_('threads').insert({
                "thread_id": thread_id,
                "project_id": project_id,
                "account_id": account_id
            }).execute()
            
            if not thread_result.error:
                print(f"✅ Created test thread: {thread_id}")
            else:
                print(f"⚠️ Couldn't create thread: {thread_result.error}")
        else:
            print(f"⚠️ Couldn't create project: {project_result.error}")
    
    except Exception as e:
        print(f"⚠️ Setup error: {str(e)}")
    
    print("📋 Using the following test environment:")
    print(f"  Account ID: {account_id}")
    print(f"  Project ID: {project_id}")
    print(f"  Thread ID: {thread_id}")
    print(f"  Sandbox ID: {sandbox_id}")
    
    return {
        "account_id": account_id,
        "project_id": project_id,
        "thread_id": thread_id,
        "sandbox_id": sandbox_id
    }

async def run_comprehensive_agent_test():
    """
    Run a comprehensive test of the agent's functionality with detailed monitoring
    to identify why tools might not be working correctly.
    """
    try:
        print("\n" + "=" * 80)
        print("🧪 COMPREHENSIVE AGENT TEST")
        print("=" * 80)
        
        # Import necessary modules
        from agent.tools.todo_generator_tool import TodoGeneratorTool
        from agent.tools.web_search_tool import WebSearchTool
        from agent.tools.sb_browser_tool import SandboxBrowserTool
        from agent.tools.sb_files_tool import SandboxFilesTool
        from agent.tools.sb_shell_tool import SandboxShellTool
        from agentpress.thread_manager import ThreadManager
        from agentpress.tool import Tool
        from sandbox.sandbox import SandboxToolsBase, Sandbox
        from daytona_sdk import SessionExecuteRequest
        import asyncio
        from unittest.mock import MagicMock, patch
        
        # Create a thread_manager and mock its DB connection
        thread_manager = ThreadManager()
        thread_manager.db = MagicMock()
        thread_manager.db.client = asyncio.Future()
        thread_manager.db.client.set_result(MagicMock())
        
        # Set up test IDs
        project_id = str(uuid.uuid4())
        thread_id = str(uuid.uuid4())
        sandbox_id = f"test-sandbox-{uuid.uuid4().hex[:8]}"
        
        print(f"\n🔍 Testing environment:")
        print(f"  Project ID: {project_id}")
        print(f"  Thread ID: {thread_id}")
        print(f"  Sandbox ID: {sandbox_id}")
        
        # Create a monitor to track tool calls and errors
        monitor = ToolCallMonitor()
        
        # Discover all tool classes
        available_tools = set()
        for subclass in Tool.__subclasses__():
            available_tools.add(subclass.__name__)
            # Also check for nested subclasses
            for nested_subclass in subclass.__subclasses__():
                available_tools.add(nested_subclass.__name__)
        monitor.record_original_tools(available_tools)
        
        # Create mock sandbox
        mock_sandbox = MagicMock(spec=Sandbox)
        mock_process = MagicMock()
        mock_fs = MagicMock()
        
        # Set properties on the sandbox mock
        mock_sandbox.process = mock_process
        mock_sandbox.fs = mock_fs
        
        # Patch SandboxToolsBase._ensure_sandbox to return our mock sandbox
        original_ensure_sandbox = SandboxToolsBase._ensure_sandbox
        
        async def mock_ensure_sandbox(self):
            self._sandbox = mock_sandbox
            self._sandbox_id = sandbox_id
            return mock_sandbox
            
        # Apply the patch
        SandboxToolsBase._ensure_sandbox = mock_ensure_sandbox
        
        print("\n🔧 Direct testing of TodoGeneratorTool...")
        
        # Create an instance of TodoGeneratorTool for testing with mocked sandbox
        todo_tool = TodoGeneratorTool(project_id, thread_manager)
        
        # Setup mock responses for file operations
        mock_todo_content = """# Task: Test Task
        
## Initial Research
- [ ] Research item 1
- [ ] Research item 2

## Implementation
- [ ] Implementation item 1
- [ ] Implementation item 2
"""
        mock_fs.download_file.return_value = mock_todo_content.encode()
        mock_fs.upload_file.return_value = None
        
        # Mock the file info check to say the file exists
        def mock_get_file_info(path):
            if path.endswith('todo.md'):
                return {"exists": True}
            raise Exception("File not found")
            
        mock_fs.get_file_info.side_effect = mock_get_file_info
        
        # Test ensure_todo_exists
        print("\n📝 Testing TodoGeneratorTool.ensure_todo_exists...")
        result = await todo_tool.ensure_todo_exists(task_description="Test Task", overwrite=True)
        print(f"  Result: {result}")
        
        # Test update_todo
        print("\n📝 Testing TodoGeneratorTool.update_todo...")
        result = await todo_tool.update_todo(
            completed_tasks=["Research item 1"], 
            new_tasks=["New task"], 
            section="Implementation"
        )
        print(f"  Result: {result}")
        
        # Examine TodoGeneratorTool methods
        print("\n📝 TodoGeneratorTool methods:")
        for method_name in dir(todo_tool):
            if not method_name.startswith('_') and callable(getattr(todo_tool, method_name)):
                print(f"  - {method_name}")
        
        # Add typical tools to the thread manager
        print("\n🔧 Registering tools with thread manager...")
        thread_manager.add_tool(SandboxShellTool, project_id=project_id, thread_manager=thread_manager)
        thread_manager.add_tool(SandboxFilesTool, project_id=project_id, thread_manager=thread_manager)
        thread_manager.add_tool(SandboxBrowserTool, project_id=project_id, thread_id=thread_id, thread_manager=thread_manager)
        thread_manager.add_tool(WebSearchTool)
        thread_manager.add_tool(TodoGeneratorTool, project_id=project_id, thread_manager=thread_manager)
        
        # Get registered tools
        registered_tools = set()

        # Get registered tools using the registry's data
        openapi_functions = thread_manager.tool_registry.get_openapi_schemas()
        xml_tags = thread_manager.tool_registry.xml_tools

        print("\nRegistered OpenAPI functions:")
        for function in openapi_functions:
            function_name = function.get('function', {}).get('name')
            if function_name:
                registered_tools.add(function_name)
                print(f"  - {function_name}")

        print("\nRegistered XML tags:")
        for tag_name in xml_tags.keys():
            registered_tools.add(tag_name.replace('-', '_'))
            print(f"  - {tag_name}")

        monitor.record_registered_tools(registered_tools)
        
        # Print comprehensive summary
        monitor.print_summary()
        
        # Test outcome based on registered tools
        todo_functions_registered = 'ensure_todo_exists' in registered_tools and 'update_todo' in registered_tools
        todo_xml_tags_registered = 'ensure-todo' in xml_tags and 'update-todo' in xml_tags

        print("\n" + "=" * 80)
        if todo_functions_registered and todo_xml_tags_registered:
            print("✅ TEST PASSED: TodoGeneratorTool was registered successfully")
            print("✅ The issue is likely in how the agent is calling the tool, not the tool registration")
            
            # Analyze tool schemas in more detail
            print("\n📋 Tool function details:")
            for function in openapi_functions:
                function_name = function.get('function', {}).get('name')
                if function_name in ['ensure_todo_exists', 'update_todo']:
                    function_desc = function.get('function', {}).get('description', '')
                    params = function.get('function', {}).get('parameters', {}).get('properties', {})
                    print(f"  - {function_name}: {function_desc}")
                    print(f"    Parameters: {', '.join(params.keys())}")
            
            # Check XML schema details
            print("\n📋 XML schema details:")
            for tag_name in ['ensure-todo', 'update-todo']:
                if tag_name in xml_tags:
                    print(f"  - {tag_name}: {xml_tags[tag_name]}")
        else:
            print("❌ TEST FAILED: TodoGeneratorTool was not properly registered")
            if not todo_functions_registered:
                print("  - Missing OpenAPI functions: ensure_todo_exists and/or update_todo")
            if not todo_xml_tags_registered:
                print("  - Missing XML tags: ensure-todo and/or update-todo")
        print("=" * 80)
        
        # Restore the original method
        SandboxToolsBase._ensure_sandbox = original_ensure_sandbox
        
        return todo_functions_registered and todo_xml_tags_registered
    
    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        logger.error(format_exc())
        return False

if __name__ == "__main__":
    asyncio.run(run_comprehensive_agent_test())
