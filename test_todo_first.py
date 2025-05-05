import asyncio
import os
import json
from uuid import uuid4

# Import necessary modules
from agentpress.thread_manager import ThreadManager
from services.supabase import DBConnection
from agent.prompt import get_system_prompt
from agent.tools.todo_generator_tool import TodoGeneratorTool
from agent.tools.sb_files_tool import SandboxFilesTool
from agent.tools.sb_shell_tool import SandboxShellTool
from agentpress.response_processor import ProcessorConfig

async def test_todo_first():
    """Test if the agent uses TodoGeneratorTool first for the task"""
    # Initialize ThreadManager
    thread_manager = ThreadManager()
    
    # Create a test thread and project
    client = await DBConnection().client
    
    try:
        # Get a valid account ID from the database
        accounts_result = await client.table('accounts').select('account_id').limit(1).execute()
        if not accounts_result.data or len(accounts_result.data) == 0:
            raise Exception("No accounts found in the database")
            
        account_id = accounts_result.data[0]['account_id']
        print(f"Using account ID: {account_id}")
        
        # Create a test project
        project_name = f"hello_world_test_{uuid4().hex[:8]}"
        project_result = await client.table('projects').insert({
            "name": project_name, 
            "account_id": account_id
        }).execute()
        
        project_id = project_result.data[0]['project_id']
        print(f"\n✨ Created test project: {project_id} ({project_name})")
        
        # Create a thread for this project
        thread_result = await client.table('threads').insert({
            'project_id': project_id,
            'account_id': account_id
        }).execute()
        
        thread_id = thread_result.data[0]['thread_id']
        print(f"✨ Created test thread: {thread_id}")
        
        # Register the necessary tools
        thread_manager.add_tool(TodoGeneratorTool, project_id=project_id, thread_manager=thread_manager)
        thread_manager.add_tool(SandboxFilesTool, project_id=project_id, thread_manager=thread_manager)
        thread_manager.add_tool(SandboxShellTool, project_id=project_id, thread_manager=thread_manager)
        
        # Add the test prompt as a user message
        test_prompt = "Build a simple hello world and test it"
        await thread_manager.add_message(
            thread_id=thread_id,
            type="user",
            content={
                "role": "user",
                "content": test_prompt
            },
            is_llm_message=True
        )
        
        print(f"\n🔄 Running agent with prompt: '{test_prompt}'")
        
        # Get the system prompt
        system_message = {"role": "system", "content": get_system_prompt()}
        
        # Run the agent and track tool calls
        tool_calls = []
        
        response = await thread_manager.run_thread(
            thread_id=thread_id,
            system_prompt=system_message,
            stream=True,
            llm_model="qwen2.5-coder:32b-instruct-q8_0",  # Use the coding model
            llm_temperature=0,
            tool_choice="auto",
            max_xml_tool_calls=1,
            processor_config=ProcessorConfig(
                xml_tool_calling=True,
                native_tool_calling=False,
                execute_tools=True,
                execute_on_stream=True,
                tool_execution_strategy="parallel",
                xml_adding_strategy="user_message"
            ),
            native_max_auto_continues=5,
            include_xml_examples=True
        )
        
        # Process the response and track tool calls
        async for chunk in response:
            if chunk.get('type') == 'tool' and 'name' in chunk:
                tool_name = chunk.get('name')
                tool_calls.append(tool_name)
                print(f"🔧 Tool called: {tool_name}")
        
        # Check if TodoGeneratorTool was called first
        if tool_calls and tool_calls[0] == 'ensure_todo_exists':
            print("\n✅ SUCCESS: TodoGeneratorTool was called first!")
        else:
            print("\n❌ FAILURE: TodoGeneratorTool was NOT called first!")
            print(f"Tool call order: {tool_calls}")
        
        # Get the messages to verify what happened
        messages = await client.table('messages').select('*').eq('thread_id', thread_id).order('created_at', asc=True).execute()
        
        # Print the conversation for analysis
        print("\n📝 Conversation:")
        for msg in messages.data:
            msg_type = msg.get('type')
            if msg_type == 'user':
                content = msg.get('content', {})
                if isinstance(content, str):
                    content = json.loads(content)
                print(f"👤 User: {content.get('content')}")
            elif msg_type == 'assistant':
                content = msg.get('content', {})
                if isinstance(content, str):
                    content = json.loads(content)
                print(f"🤖 Assistant: {content.get('content')[:100]}...")
            elif msg_type == 'tool':
                print(f"🔧 Tool ({msg.get('name')}): {msg.get('content')[:100]}...")
        
    except Exception as e:
        print(f"Error in test: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_todo_first())
