# Complete Agent Tool Examples

This guide provides practical examples for all available tools to ensure the agent knows how to use them correctly.

## Todo Management Tools

### Creating a Todo List
```xml
<ensure-todo overwrite="true">
Create a new React web application with user authentication
</ensure-todo>
```

### Updating a Todo List
```xml
<update-todo section="Implementation">
    <completed_tasks>
        ["Initialize React project", "Create component structure"]
    </completed_tasks>
    <new_tasks>
        ["Add user authentication form", "Implement API calls"]
    </new_tasks>
</update-todo>
```

## File Management Tools

### Creating a File
```xml
<create-file file_path="src/components/Login.js">
import React, { useState } from 'react';

function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log('Login submitted:', username, password);
  };

  return (
    <div className="login-form">
      <h2>Login</h2>
      <form onSubmit={handleSubmit}>
        <div>
          <label>Username:</label>
          <input 
            type="text" 
            value={username} 
            onChange={(e) => setUsername(e.target.value)}
          />
        </div>
        <div>
          <label>Password:</label>
          <input 
            type="password" 
            value={password} 
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        <button type="submit">Login</button>
      </form>
    </div>
  );
}

export default Login;
</create-file>
```

### Editing Part of a File
```xml
<str-replace file_path="src/App.js">
    <old_str>function App() {
  return (
    <div className="App">
      <header className="App-header">
        <p>
          Edit <code>src/App.js</code> and save to reload.
        </p>
      </header>
    </div>
  );
}</old_str>
    <new_str>function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>My React App</h1>
      </header>
      <main>
        <Login />
      </main>
    </div>
  );
}</new_str>
</str-replace>
```

### Rewriting an Entire File
```xml
<full-file-rewrite file_path="src/App.js">
import React from 'react';
import './App.css';
import Login from './components/Login';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>My React App</h1>
      </header>
      <main>
        <Login />
      </main>
    </div>
  );
}

export default App;
</full-file-rewrite>
```

### Deleting a File
```xml
<delete-file file_path="src/logo.svg" />
```

## Browser Tools

### Navigating to a Website
```xml
<browser-navigate-to>
https://react.dev/
</browser-navigate-to>
```

### Going Back
```xml
<browser-go-back />
```

### Clicking an Element
```xml
<browser-click-element>
0
</browser-click-element>
```

### Typing Text
```xml
<browser-input-text index="0">
search query
</browser-input-text>
```

### Pressing Keys
```xml
<browser-send-keys>
Enter
</browser-send-keys>
```

## Command Line Tools

### Running a Command
```xml
<execute-command>
npm install react-router-dom
</execute-command>
```

### Running a Command in a Specific Folder
```xml
<execute-command folder="frontend">
npm start
</execute-command>
```

## Web Search Tools

### Performing a Web Search
```xml
<web-search query="React authentication best practices" num_results="5" />
```

### Scraping a Webpage
```xml
<scrape-webpage url="https://react.dev/learn" />
```

## Important Notes

1. Always use the proper XML format with opening and closing tags
2. Make sure to include all required attributes for each tool
3. Use JSON arrays for lists (in the todo tools)
4. Create a todo list at the beginning of a task
5. Update the todo list as you make progress
6. Always validate file paths before creating or editing files 