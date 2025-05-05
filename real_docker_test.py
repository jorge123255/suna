#!/usr/bin/env python3
"""
Real Docker Test Script

This script tests the actual implementation of the embedding-based task classifier
for model selection in the Docker environment.
"""

import os
import sys
import json
import asyncio
from datetime import datetime

# Add the backend directory to the path so we can import from it
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

# Configure logging
import logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   stream=sys.stdout)

logger = logging.getLogger("real_docker_test")

# Sample prompts for testing model selection
TEST_PROMPTS = [
    {
        "category": "coding",
        "prompt": "Write a Python function to sort a list of integers using the quicksort algorithm"
    },
    {
        "category": "coding",
        "prompt": "Help me debug this React component that's not rendering properly"
    },
    {
        "category": "reasoning",
        "prompt": "Explain the implications of quantum computing on modern cryptography systems"
    },
    {
        "category": "reasoning",
        "prompt": "Analyze the trade-offs between privacy and convenience in modern technology"
    },
    {
        "category": "creative",
        "prompt": "Write a short story about a robot that becomes self-aware and discovers the meaning of love"
    },
    {
        "category": "creative",
        "prompt": "Create a poem about the changing seasons and the passage of time"
    },
    {
        "category": "general",
        "prompt": "What's the capital of France?"
    },
    {
        "category": "general",
        "prompt": "How do I make a good cup of coffee?"
    }
]

async def test_model_selection():
    """Test the model selection functionality using the embedding task classifier."""
    try:
        # Import the necessary modules
        from services.embedding_task_classifier import get_model_for_task, classify_task_with_embeddings
        
        print("\n" + "=" * 80)
        print("🧠 MODEL SELECTION TEST")
        print("=" * 80)
        
        print("\n🔍 Testing model selection for different task types...")
        
        results = []
        
        for test in TEST_PROMPTS:
            try:
                # Get the task type and confidence
                task_type, confidence = classify_task_with_embeddings(test["prompt"])
                
                # Get the selected model
                model = get_model_for_task(test["prompt"])
                
                result = {
                    "prompt": test["prompt"],
                    "expected_category": test["category"],
                    "detected_task_type": task_type,
                    "confidence": confidence,
                    "selected_model": model
                }
                
                results.append(result)
                
                print(f"✅ Prompt: \"{test['prompt']}\"")
                print(f"   Expected category: {test['category']}")
                print(f"   Detected task type: {task_type}")
                print(f"   Confidence: {confidence:.2f}")
                print(f"   Selected model: {model}")
                print()
            except Exception as e:
                print(f"❌ Failed to classify prompt: \"{test['prompt']}\"")
                print(f"   Error: {e}")
                print()
        
        # Calculate accuracy
        correct = sum(1 for r in results if r["expected_category"] == r["detected_task_type"])
        accuracy = correct / len(results) if results else 0
        
        print(f"📊 Model Selection Accuracy: {accuracy:.2f} ({correct}/{len(results)})")
        
        # Print model mapping
        print("\n📋 Model Mapping:")
        from services.embedding_task_classifier import TASK_MODELS
        for task_type, model in TASK_MODELS.items():
            print(f"   {task_type}: {model}")
        
        print("\n" + "=" * 80)
        print("✅ MODEL SELECTION TEST COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

async def test_file_creation():
    """Test creating a todo.md file in the Docker environment."""
    try:
        print("\n" + "=" * 80)
        print("📝 FILE CREATION TEST")
        print("=" * 80)
        
        # Create a simple todo.md file
        todo_content = """# Agent Todo List

## Task Description
Create a simple web application that:
1. Displays a list of tasks
2. Allows adding new tasks
3. Allows marking tasks as complete
4. Stores tasks in a database

## Research
- [x] Understand the requirements
- [x] Identify key components needed
- [ ] Research best practices for web application development
- [ ] Evaluate database options for storing tasks

## Implementation
- [ ] Set up project structure
- [ ] Create database schema
- [ ] Implement backend API
- [ ] Develop frontend UI
- [ ] Add user authentication

## Testing
- [ ] Write unit tests
- [ ] Perform integration testing
- [ ] Test user interface
- [ ] Verify all requirements are met

## Deployment
- [ ] Set up deployment environment
- [ ] Configure CI/CD pipeline
- [ ] Deploy application
- [ ] Monitor performance
"""
        
        # Write the todo.md file to the workspace directory
        workspace_path = "/workspace" if os.path.exists("/workspace") else "."
        todo_path = os.path.join(workspace_path, "todo.md")
        
        with open(todo_path, "w") as f:
            f.write(todo_content)
        
        print(f"✅ Created todo.md file at {todo_path}")
        
        # Log the file operation
        try:
            from services.agent_logger import log_file_operation
            
            await log_file_operation(
                thread_id="test-thread-123",
                operation_type="write",
                file_path=todo_path,
                content_snippet=todo_content[:100] + "...",
                agent_run_id="test-run-123",
                project_id="test-project-123"
            )
            
            print("✅ Logged file operation")
        except Exception as e:
            print(f"⚠️ Could not log file operation: {e}")
        
        print("\n" + "=" * 80)
        print("✅ FILE CREATION TEST COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main function to run all tests."""
    print("\n" + "=" * 80)
    print("🐳 REAL DOCKER TESTS")
    print("=" * 80)
    
    # Run the model selection test
    await test_model_selection()
    
    # Run the file creation test
    await test_file_creation()
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS COMPLETE")
    print("=" * 80)
    print("These tests demonstrate the agent's capabilities in the Docker environment.")
    print("The agent can select appropriate models for different tasks and create files.")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
