# Example Agent Workflow with TodoList

This guide demonstrates a complete workflow for an agent task, showing how to properly use the TodoList tool throughout the process.

## Task: Create a simple React login form

### Step 1: Create a todo list for the task

```xml
<ensure-todo overwrite="true">
Create a simple React login form with username and password fields
</ensure-todo>
```

### Step 2: Set up the project structure

```xml
<execute-command>
mkdir -p react-login-app/src/components
cd react-login-app
npm init -y
npm install react react-dom
</execute-command>
```

### Step 3: Update the todo list with completed and new tasks

```xml
<update-todo section="Implementation">
    <completed_tasks>
        ["Set up project structure"]
    </completed_tasks>
    <new_tasks>
        ["Create Login component", "Create App component", "Set up basic styling"]
    </new_tasks>
</update-todo>
```

### Step 4: Create the Login component

```xml
<create-file file_path="react-login-app/src/components/Login.js">
import React, { useState } from 'react';

function Login({ onSubmit }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({ username, password });
  };

  return (
    <div className="login-form">
      <h2>Login</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="username">Username:</label>
          <input 
            id="username"
            type="text" 
            value={username} 
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="password">Password:</label>
          <input 
            id="password"
            type="password" 
            value={password} 
            onChange={(e) => setPassword(e.target.value)}
            required
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

### Step 5: Update the todo list again

```xml
<update-todo section="Implementation">
    <completed_tasks>
        ["Set up project structure", "Create Login component"]
    </completed_tasks>
    <new_tasks>
        ["Create App component", "Set up basic styling", "Create index.js entry point"]
    </new_tasks>
</update-todo>
```

### Step 6: Create the App component

```xml
<create-file file_path="react-login-app/src/App.js">
import React from 'react';
import Login from './components/Login';
import './App.css';

function App() {
  const handleLogin = (credentials) => {
    console.log('Login submitted:', credentials);
    alert(`Login attempted with username: ${credentials.username}`);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>React Login Example</h1>
      </header>
      <main>
        <Login onSubmit={handleLogin} />
      </main>
    </div>
  );
}

export default App;
</create-file>
```

### Step 7: Create basic styling

```xml
<create-file file_path="react-login-app/src/App.css">
.App {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  font-family: Arial, sans-serif;
}

.App-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-form {
  max-width: 400px;
  margin: 0 auto;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 5px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

.form-group input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
}

button {
  background-color: #4CAF50;
  color: white;
  padding: 10px 15px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
}

button:hover {
  background-color: #45a049;
}
</create-file>
```

### Step 8: Create the entry point file

```xml
<create-file file_path="react-login-app/src/index.js">
import React from 'react';
import ReactDOM from 'react-dom';
import App from './App';

ReactDOM.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
  document.getElementById('root')
);
</create-file>
```

### Step 9: Final update to the todo list

```xml
<update-todo section="Implementation">
    <completed_tasks>
        ["Set up project structure", "Create Login component", "Create App component", "Set up basic styling", "Create index.js entry point"]
    </completed_tasks>
    <new_tasks>
        ["Add form validation", "Connect to backend API"]
    </new_tasks>
</update-todo>
```

### Step 10: Summarize the work done

This example demonstrates how to:

1. Start with a clear todo list that outlines the main task
2. Update the todo list after completing each sub-task
3. Add new tasks to the todo list as they are identified
4. Track progress throughout the implementation
5. Complete the task while maintaining an organized workflow

This workflow ensures that all steps are tracked and the agent maintains focus on completing the required tasks in a structured manner. 