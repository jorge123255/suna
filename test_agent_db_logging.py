#!/usr/bin/env python3
"""
Test script to verify that the agent system is working correctly with database logging.
This script tests:
1. Agent initialization and execution
2. Database logging of agent actions
3. Model selection functionality
"""

import asyncio
import os
import sys
import uuid
import json
from datetime import datetime

# Add the backend directory to the path so we can import modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Import required modules
from services.agent_logger import log_agent_action, log_agent_start, log_agent_stop
from services.model_selection_logger import log_model_selection
from utils.config import config, EnvMode

async def test_agent_db_logging():
    """Test agent database logging functionality."""
    print("Starting agent database logging test...")
    
    # Generate unique IDs for testing
    thread_id = str(uuid.uuid4())
    agent_run_id = str(uuid.uuid4())
    project_id = str(uuid.uuid4())
    
    print(f"Test IDs - Thread: {thread_id}, Agent Run: {agent_run_id}, Project: {project_id}")
    
    # Test 1: Log agent start
    print("\n1. Testing agent_start logging...")
    try:
        log_agent_start(
            thread_id=thread_id,
            agent_run_id=agent_run_id,
            project_id=project_id,
            model_name="qwen2.5:32b-instruct-q4_K_M",
            enable_thinking=False,
            reasoning_effort="low",
            enable_context_manager=False
        )
        print("✅ Successfully logged agent start")
    except Exception as e:
        print(f"❌ Error logging agent start: {str(e)}")
    
    # Test 2: Log agent action
    print("\n2. Testing agent_action logging...")
    try:
        action_details = {
            "action": "test_action",
            "timestamp": datetime.now().isoformat(),
            "details": "This is a test action to verify database logging"
        }
        
        log_agent_action(
            thread_id=thread_id,
            action_type="test",
            action_details=action_details,
            agent_run_id=agent_run_id,
            project_id=project_id
        )
        print("✅ Successfully logged agent action")
    except Exception as e:
        print(f"❌ Error logging agent action: {str(e)}")
    
    # Test 3: Log model selection
    print("\n3. Testing model_selection logging...")
    try:
        await log_model_selection(
            thread_id=thread_id,
            prompt_text="Write a Python function to calculate Fibonacci numbers",
            classified_task_type="coding",
            confidence_score=0.95,
            selected_model="qwen2.5-coder:32b-instruct-q8_0",
            prompt_tokens=42
        )
        print("✅ Successfully logged model selection")
    except Exception as e:
        print(f"❌ Error logging model selection: {str(e)}")
    
    # Test 4: Log agent stop
    print("\n4. Testing agent_stop logging...")
    try:
        log_agent_stop(
            thread_id=thread_id,
            agent_run_id=agent_run_id,
            project_id=project_id,
            status="completed",
            duration_ms=1500
        )
        print("✅ Successfully logged agent stop")
    except Exception as e:
        print(f"❌ Error logging agent stop: {str(e)}")
    
    print("\nAgent database logging test completed!")

if __name__ == "__main__":
    # Set environment mode to local for testing
    config.ENV_MODE = EnvMode.LOCAL
    
    # Run the test
    asyncio.run(test_agent_db_logging())
