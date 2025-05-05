#!/usr/bin/env python3
"""
Real Agent Test

This script tests the actual agent's behavior with the updated system prompt
to verify if it uses the TodoGeneratorTool first when given the task
"Build a simple hello world and test it".
"""

import os
import sys
import json
import asyncio
import time
import uuid
from typing import List, Dict, Any, Optional

# Add the backend directory to the path so we can import from it
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

# Configure logging
import logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   stream=sys.stdout)

logger = logging.getLogger("real_agent_test")

class ToolCallMonitor:
    """Monitors tool calls made by the agent"""
    
    def __init__(self):
        self.tool_calls = []
        self.first_tool = None
        
    def add_tool_call(self, tool_name: str, tool_args: Dict[str, Any]):
        """Record a tool call"""
        self.tool_calls.append({
            "tool_name": tool_name,
            "args": tool_args,
            "timestamp": time.time()
        })
        
        # Record the first tool call
        if not self.first_tool:
            self.first_tool = tool_name
            
    def get_first_tool(self) -> Optional[str]:
        """Get the name of the first tool called"""
        return self.first_tool
    
    def print_tool_calls(self):
        """Print all recorded tool calls"""
        print("\n📊 Tool Call Summary:")
        if not self.tool_calls:
            print("No tool calls recorded")
            return
            
        for i, call in enumerate(self.tool_calls):
            print(f"{i+1}. {call['tool_name']} - Args: {json.dumps(call['args'], indent=2)}")

async def run_real_agent_test():
    """
    Run a real test of the agent's behavior with the updated system prompt.
    This test will:
    1. Initialize the agent with the real system prompt
    2. Run the agent with the "Build a simple hello world and test it" task
    3. Monitor which tools are called and in what order
    4. Verify if TodoGeneratorTool is called first
    """
    try:
        print("\n" + "=" * 80)
        print("🧪 REAL AGENT TEST")
        print("=" * 80)
        
        # Import necessary modules
        from agent.run import run_agent
        from agent.prompt import get_system_prompt
        from agentpress.thread_manager import ThreadManager
        from services.supabase import DBConnection
        
        # Create a tool call monitor
        monitor = ToolCallMonitor()
        
        # Initialize the database connection
        client = await DBConnection().client
        
        # Create a test account if needed
        print("\n🔍 Checking for existing test account...")
        accounts = await client.table('accounts').select('account_id').limit(1).execute()
        
        if not accounts.data or len(accounts.data) == 0:
            print("❌ No accounts found in database. Creating a test account...")
            account_result = await client.table('accounts').insert({
                "account_id": str(uuid.uuid4()),
                "name": "Test Account",
                "email": "test@example.com"
            }).execute()
            account_id = account_result.data[0]['account_id']
            print(f"✅ Created test account: {account_id}")
        else:
            account_id = accounts.data[0]['account_id']
            print(f"✅ Using existing account: {account_id}")
        
        # Create a test project
        print("\n🔍 Creating test project...")
        project_name = f"hello_world_test_{uuid.uuid4().hex[:8]}"
        project_result = await client.table('projects').insert({
            "project_id": str(uuid.uuid4()),
            "name": project_name,
            "account_id": account_id,
            "sandbox": {
                "id": "test-sandbox-id",
                "status": "running"
            }
        }).execute()
        
        project_id = project_result.data[0]['project_id']
        print(f"✅ Created test project: {project_id} ({project_name})")
        
        # Create a test thread
        print("\n🔍 Creating test thread...")
        thread_result = await client.table('threads').insert({
            "thread_id": str(uuid.uuid4()),
            "project_id": project_id,
            "account_id": account_id
        }).execute()
        
        thread_id = thread_result.data[0]['thread_id']
        print(f"✅ Created test thread: {thread_id}")
        
        # Add the test prompt as a user message
        print("\n🔍 Adding test prompt to thread...")
        test_prompt = "Build a simple hello world and test it"
        await client.table('messages').insert({
            "message_id": str(uuid.uuid4()),
            "thread_id": thread_id,
            "type": "user",
            "content": json.dumps({
                "role": "user",
                "content": test_prompt
            }),
            "is_llm_message": True
        }).execute()
        print(f"✅ Added test prompt: '{test_prompt}'")
        
        # Patch the tool execution to monitor tool calls
        original_execute_tool = ThreadManager._execute_tool
        
        async def patched_execute_tool(self, tool_call):
            # Extract tool name and args
            tool_name = tool_call.get('function_name') or tool_call.get('xml_tag_name')
            tool_args = tool_call.get('arguments', {})
            
            # Record the tool call
            monitor.add_tool_call(tool_name, tool_args)
            print(f"🔧 Tool called: {tool_name}")
            
            # Call the original method
            return await original_execute_tool(self, tool_call)
        
        # Apply the patch
        ThreadManager._execute_tool = patched_execute_tool
        
        # Print the system prompt instruction
        system_prompt = get_system_prompt()
        print("\n📝 System prompt instruction:")
        print("-" * 80)
        for line in system_prompt.split("\n")[:10]:  # Print first 10 lines
            if "TodoGeneratorTool" in line:
                print(line)
        print("-" * 80)
        
        # Run the agent
        print("\n🤖 Running agent with the task...")
        
        # Set a timeout for the agent run
        timeout_seconds = 180
        print(f"⏱️ Setting timeout to {timeout_seconds} seconds")
        
        try:
            # Run with timeout
            agent_run_id = str(uuid.uuid4())
            
            # Create a generator to capture the agent's output
            agent_output = run_agent(
                thread_id=thread_id,
                project_id=project_id,
                stream=True,
                native_max_auto_continues=5,
                max_iterations=10,  # Limit iterations for testing
                model_name="qwen2.5-coder:32b-instruct-q8_0",  # Use the coding model
                enable_thinking=False,
                reasoning_effort="low",
                enable_context_manager=True,
                agent_run_id=agent_run_id
            )
            
            # Process the output with timeout
            async def process_output():
                async for chunk in agent_output:
                    # Just consume the chunks, we're only interested in the tool calls
                    if chunk.get('type') == 'status':
                        print(f"Status: {chunk.get('status')} - {chunk.get('message', '')}")
                
            await asyncio.wait_for(process_output(), timeout=timeout_seconds)
                
        except asyncio.TimeoutError:
            print(f"⚠️ Agent run timed out after {timeout_seconds} seconds")
        except Exception as e:
            print(f"❌ Error running agent: {e}")
        
        # Restore the original method
        ThreadManager._execute_tool = original_execute_tool
        
        # Print the tool calls
        monitor.print_tool_calls()
        
        # Check if TodoGeneratorTool was called first
        first_tool = monitor.get_first_tool()
        if first_tool == "ensure_todo_exists":
            print("\n✅ SUCCESS: TodoGeneratorTool was called first!")
        else:
            print(f"\n❌ FAILURE: First tool called was: {first_tool}")
        
        # Query the messages to see what happened
        print("\n🔍 Checking messages in thread...")
        messages = await client.table('messages').select('*').eq('thread_id', thread_id).order('created_at', asc=True).execute()
        
        print(f"Found {len(messages.data)} messages in thread")
        
        # Print the conversation
        print("\n📝 Conversation:")
        for msg in messages.data:
            msg_type = msg.get('type')
            if msg_type == 'user':
                content = msg.get('content', {})
                if isinstance(content, str):
                    try:
                        content = json.loads(content)
                    except:
                        pass
                print(f"👤 User: {content.get('content') if isinstance(content, dict) else content}")
            elif msg_type == 'assistant':
                content = msg.get('content', {})
                if isinstance(content, str):
                    try:
                        content = json.loads(content)
                    except:
                        pass
                print(f"🤖 Assistant: {content.get('content')[:100] if isinstance(content, dict) else content[:100]}...")
            elif msg_type == 'tool':
                tool_name = msg.get('name', 'unknown')
                print(f"🔧 Tool ({tool_name}): {msg.get('content', '')[:100]}...")
        
        print("\n" + "=" * 80)
        print("✅ REAL AGENT TEST COMPLETE")
        print("=" * 80)
        
        return first_tool == "ensure_todo_exists"
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(run_real_agent_test())
