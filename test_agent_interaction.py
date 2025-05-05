#!/usr/bin/env python3
"""
Test script to demonstrate agent-LLM interactions, reasoning process, and todo.md generation.
This script simulates a conversation with the agent and shows the reasoning process.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# Add the backend directory to the path so we can import from it
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

# Import necessary modules from the backend
from agent.run import run_agent
from agent.tools.todo_generator_tool import TodoGeneratorTool
from agentpress.thread_manager import ThreadManager
from services.supabase import DBConnection
from services.agent_logger import log_agent_action
from utils.logger import logger

# Configure logging to show detailed output
import logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   stream=sys.stdout)

# Sample task to test the agent
SAMPLE_TASK = """
Create a simple web server in Python that:
1. Serves a "Hello, World!" page at the root URL
2. Has an endpoint at /time that shows the current time
3. Has a /counter endpoint that increments a counter each time it's visited
"""

class AgentTester:
    """Test harness for the agent to demonstrate interactions and reasoning."""
    
    def __init__(self):
        self.thread_id = f"test_thread_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.project_id = f"test_project_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.db = DBConnection()
        self.thread_manager = ThreadManager()
        self.messages = []
        self.tool_calls = []
        
    async def setup(self):
        """Set up the test environment."""
        client = await self.db.client
        
        # Create a test account if needed
        account_result = await client.table("accounts").insert({
            "name": "Test Account",
            "user_id": "test_user"
        }).execute()
        
        if not account_result.data:
            print("Failed to create test account")
            return False
            
        account_id = account_result.data[0]["id"]
        
        # Create a test thread
        thread_result = await client.table("threads").insert({
            "id": self.thread_id,
            "account_id": account_id,
            "name": "Test Thread"
        }).execute()
        
        if not thread_result.data:
            print("Failed to create test thread")
            return False
        
        # Create a test project with sandbox info
        project_result = await client.table("projects").insert({
            "project_id": self.project_id,
            "thread_id": self.thread_id,
            "account_id": account_id,
            "name": "Test Project",
            "sandbox": {
                "id": "test_sandbox",
                "password": "test_password"
            }
        }).execute()
        
        if not project_result.data:
            print("Failed to create test project")
            return False
        
        # Add the initial user message
        message_result = await client.table("messages").insert({
            "thread_id": self.thread_id,
            "type": "user",
            "content": SAMPLE_TASK
        }).execute()
        
        if not message_result.data:
            print("Failed to create initial message")
            return False
            
        print(f"✅ Test environment set up successfully")
        print(f"Thread ID: {self.thread_id}")
        print(f"Project ID: {self.project_id}")
        return True
        
    async def run_test(self):
        """Run the agent and capture its interactions."""
        print("\n🚀 Starting agent test run...")
        print(f"Task: {SAMPLE_TASK}")
        print("\n📝 Agent will now process this task and create a todo.md file...")
        
        # Set up a message collector to capture agent outputs
        async def message_collector(message):
            if isinstance(message, dict):
                message_type = message.get("type")
                if message_type == "assistant":
                    content = message.get("content", "")
                    if content:
                        print(f"\n🤖 AGENT: {content[:200]}..." if len(content) > 200 else f"\n🤖 AGENT: {content}")
                        self.messages.append(message)
                elif message_type == "tool":
                    tool_name = message.get("name", "unknown_tool")
                    print(f"\n🛠️  TOOL ({tool_name}): {message.get('content', '')[:100]}...")
                    self.tool_calls.append(message)
                elif message_type == "thinking":
                    print(f"\n💭 THINKING: {message.get('content', '')[:150]}...")
                elif message_type == "status":
                    status = message.get("status")
                    if status == "stopped":
                        print(f"\n⏹️  AGENT STOPPED: {message.get('message', 'No reason provided')}")
            return message
        
        # Run the agent with the test task
        agent_run_id = f"test_run_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Log the start of the agent run
        log_agent_action(
            thread_id=self.thread_id,
            action_type="agent_start",
            action_details={
                "task": SAMPLE_TASK,
                "test_run": True
            },
            agent_run_id=agent_run_id,
            project_id=self.project_id
        )
        
        try:
            # Run the agent with our task
            async for chunk in run_agent(
                thread_id=self.thread_id,
                project_id=self.project_id,
                stream=True,
                thread_manager=self.thread_manager,
                model_name="qwen2.5:32b-instruct-q4_K_M",  # Use the default model
                enable_thinking=True,  # Enable thinking to see reasoning
                reasoning_effort="high",  # Use high reasoning effort
                enable_context_manager=True,
                agent_run_id=agent_run_id
            ):
                await message_collector(chunk)
        except Exception as e:
            print(f"❌ Error running agent: {e}")
            return False
            
        # Log the completion of the agent run
        log_agent_action(
            thread_id=self.thread_id,
            action_type="agent_stop",
            action_details={
                "status": "completed",
                "message_count": len(self.messages),
                "tool_call_count": len(self.tool_calls)
            },
            agent_run_id=agent_run_id,
            project_id=self.project_id
        )
        
        print("\n✅ Agent test run completed")
        return True
        
    async def analyze_results(self):
        """Analyze the results of the agent run."""
        print("\n📊 Analyzing agent run results...")
        
        # Check if todo.md was created
        todo_created = any(
            call.get("name") == "ensure_todo_exists" or 
            call.get("name") == "create_file" and "todo.md" in call.get("content", "")
            for call in self.tool_calls
        )
        
        print(f"Todo.md created: {'✅ Yes' if todo_created else '❌ No'}")
        
        # Check if the agent used reasoning
        reasoning_used = any("thinking" in msg.get("type", "") for msg in self.messages)
        print(f"Agent used reasoning: {'✅ Yes' if reasoning_used else '❌ No'}")
        
        # Check if the agent completed the task
        task_completed = any(
            "web server" in call.get("content", "") and 
            "python" in call.get("content", "").lower() and
            "execute" in call.get("name", "").lower()
            for call in self.tool_calls
        )
        
        print(f"Task completed: {'✅ Yes' if task_completed else '❌ No'}")
        
        # Summarize tool usage
        tool_usage = {}
        for call in self.tool_calls:
            tool_name = call.get("name", "unknown")
            tool_usage[tool_name] = tool_usage.get(tool_name, 0) + 1
            
        print("\n🛠️  Tool usage summary:")
        for tool, count in tool_usage.items():
            print(f"  - {tool}: {count} calls")
            
        return {
            "todo_created": todo_created,
            "reasoning_used": reasoning_used,
            "task_completed": task_completed,
            "tool_usage": tool_usage
        }
        
    async def cleanup(self):
        """Clean up test resources."""
        try:
            client = await self.db.client
            
            # Delete test project
            await client.table("projects").delete().eq("project_id", self.project_id).execute()
            
            # Delete test thread and messages
            await client.table("messages").delete().eq("thread_id", self.thread_id).execute()
            await client.table("threads").delete().eq("id", self.thread_id).execute()
            
            print("\n🧹 Test resources cleaned up")
            return True
        except Exception as e:
            print(f"❌ Error cleaning up: {e}")
            return False

async def main():
    """Main function to run the test."""
    print("=" * 80)
    print("🧪 AGENT INTERACTION TEST")
    print("=" * 80)
    
    tester = AgentTester()
    
    try:
        # Set up the test environment
        if not await tester.setup():
            print("❌ Failed to set up test environment")
            return
            
        # Run the test
        if not await tester.run_test():
            print("❌ Failed to run agent test")
            return
            
        # Analyze the results
        results = await tester.analyze_results()
        
        print("\n" + "=" * 80)
        print("📋 TEST SUMMARY")
        print("=" * 80)
        print(f"Todo.md Created: {'✅' if results['todo_created'] else '❌'}")
        print(f"Reasoning Used: {'✅' if results['reasoning_used'] else '❌'}")
        print(f"Task Completed: {'✅' if results['task_completed'] else '❌'}")
        
        # Cleanup test resources
        await tester.cleanup()
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
