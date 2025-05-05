# TodoList Tool Usage Guide for Agents

## Overview
This guide demonstrates how to properly use the TodoList tools in your agent workflows. The TodoList system helps you track tasks and maintain an organized workflow.

## Available Todo Tools

### 1. ensure-todo
This tool ensures a todo.md file exists with your task description.

**Correct Format:**
```xml
<ensure-todo overwrite="false">
Create a React application with a login page
</ensure-todo>
```

**Parameters:**
- `overwrite`: Set to "true" to replace an existing todo, or "false" to keep it if it exists
- Content: The main task description

### 2. update-todo
This tool updates the existing todo.md file with completed tasks and/or new tasks.

**Correct Format:**
```xml
<update-todo section="Implementation">
    <completed_tasks>
        ["Set up React project", "Create component structure"]
    </completed_tasks>
    <new_tasks>
        ["Implement login form validation", "Add error handling"]
    </new_tasks>
</update-todo>
```

**Parameters:**
- `section`: The section of the todo list to update (e.g., "Research", "Implementation", "Testing")
- `completed_tasks`: JSON array of tasks that have been completed
- `new_tasks`: JSON array of new tasks to add

## Best Practices

1. **Always create a todo list first** using `ensure-todo` at the beginning of a task
2. **Use proper JSON arrays** in the completed_tasks and new_tasks elements
3. **Update the todo list** whenever you complete a task
4. **Add new tasks** when you discover additional work needed
5. **Use meaningful section names** to organize your todo list

## Common Errors to Avoid

1. Using incorrect XML formatting for tool calls
2. Forgetting to include the "overwrite" attribute
3. Not using proper JSON array format for tasks
4. Trying to update a todo list that doesn't exist yet

Remember that each task in the completed_tasks and new_tasks arrays should be a string, and the entire array should be valid JSON. 