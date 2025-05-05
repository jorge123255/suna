"""
Simple test script to demonstrate a Hello World program with proper todo list generation.
This script simulates what the agent should do when given the task "Build a simple hello world and test it".
"""

import os
import sys

# Simulate the TodoGeneratorTool functionality
def create_todo(task_description):
    """Create a todo.md file for the task"""
    todo_content = f"""# Task: {task_description}

## Initial Research
- [ ] Understand the requirements for a Hello World program
- [ ] Determine the programming language to use

## Implementation
- [ ] Create the Hello World program file
- [ ] Implement the code to display "Hello, World!"
- [ ] Save the file

## Testing
- [ ] Run the program
- [ ] Verify the output shows "Hello, World!"

## Delivery
- [ ] Clean up code
- [ ] Add documentation
- [ ] Prepare final deliverables
"""
    
    with open("todo.md", "w") as f:
        f.write(todo_content)
    
    print("✅ Created todo.md file")
    return todo_content

def implement_hello_world():
    """Implement a simple Hello World program"""
    # Create a Python Hello World program
    with open("hello_world.py", "w") as f:
        f.write("""#!/usr/bin/env python3
# A simple Hello World program

def main():
    print("Hello, World!")
    
if __name__ == "__main__":
    main()
""")
    
    print("✅ Created hello_world.py")

def test_hello_world():
    """Test the Hello World program"""
    print("\n🧪 Testing hello_world.py...")
    print("Output:")
    print("-" * 40)
    os.system("python hello_world.py")
    print("-" * 40)
    print("✅ Test completed")

def update_todo():
    """Update the todo.md file to mark tasks as completed"""
    if not os.path.exists("todo.md"):
        print("❌ todo.md does not exist")
        return
    
    with open("todo.md", "r") as f:
        content = f.read()
    
    # Mark all tasks as completed
    content = content.replace("- [ ]", "- [x]")
    
    with open("todo.md", "w") as f:
        f.write(content)
    
    print("✅ Updated todo.md - all tasks marked as completed")

def main():
    """Main function to demonstrate the Hello World task flow"""
    print("\n🤖 AGENT SIMULATION: Build a simple hello world and test it")
    print("=" * 60)
    
    print("\n1️⃣ First step: Create a todo list")
    create_todo("Build a simple hello world and test it")
    
    print("\n2️⃣ Second step: Implement the Hello World program")
    implement_hello_world()
    
    print("\n3️⃣ Third step: Test the Hello World program")
    test_hello_world()
    
    print("\n4️⃣ Fourth step: Update the todo list")
    update_todo()
    
    print("\n✨ Task completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    # Create a clean working directory
    os.makedirs("hello_world_test", exist_ok=True)
    os.chdir("hello_world_test")
    
    try:
        main()
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Show the final files
    print("\n📂 Final files:")
    for file in os.listdir("."):
        print(f"  - {file}")
