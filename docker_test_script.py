#!/usr/bin/env python3
"""
Simple test script to demonstrate how the agent executes code in the sandbox.
This script doesn't rely on any custom modules we created.
"""

import asyncio
import json
import os
import sys
from datetime import datetime

# Add the backend directory to the path so we can import from it
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

# Configure logging to show detailed output
import logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   stream=sys.stdout)

# Sample Python web server code to test
SAMPLE_WEB_SERVER = """
from http.server import BaseHTTPRequestHandler, HTTPServer
import time

# Counter for tracking visits to /counter endpoint
visit_counter = 0

class SimpleServer(BaseHTTPRequestHandler):
    def do_GET(self):
        global visit_counter
        
        if self.path == '/':
            # Root path - serve "Hello, World!"
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(bytes("<html><head><title>Hello World</title></head>", "utf-8"))
            self.wfile.write(bytes("<body><h1>Hello, World!</h1>", "utf-8"))
            self.wfile.write(bytes("<p>This is a simple web server created by the Suna agent.</p>", "utf-8"))
            self.wfile.write(bytes("<p>Try these endpoints:</p>", "utf-8"))
            self.wfile.write(bytes("<ul>", "utf-8"))
            self.wfile.write(bytes("<li><a href='/time'>Current Time</a></li>", "utf-8"))
            self.wfile.write(bytes("<li><a href='/counter'>Visit Counter</a></li>", "utf-8"))
            self.wfile.write(bytes("</ul>", "utf-8"))
            self.wfile.write(bytes("</body></html>", "utf-8"))
        
        elif self.path == '/time':
            # Time endpoint - show current time
            current_time = time.strftime("%H:%M:%S")
            current_date = time.strftime("%Y-%m-%d")
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(bytes("<html><head><title>Current Time</title></head>", "utf-8"))
            self.wfile.write(bytes("<body><h1>Current Time</h1>", "utf-8"))
            self.wfile.write(bytes(f"<p>Date: {current_date}</p>", "utf-8"))
            self.wfile.write(bytes(f"<p>Time: {current_time}</p>", "utf-8"))
            self.wfile.write(bytes("<p><a href='/'>Back to Home</a></p>", "utf-8"))
            self.wfile.write(bytes("</body></html>", "utf-8"))
        
        elif self.path == '/counter':
            # Counter endpoint - increment and show counter
            visit_counter += 1
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(bytes("<html><head><title>Visit Counter</title></head>", "utf-8"))
            self.wfile.write(bytes("<body><h1>Visit Counter</h1>", "utf-8"))
            self.wfile.write(bytes(f"<p>This page has been visited {visit_counter} times.</p>", "utf-8"))
            self.wfile.write(bytes("<p><a href='/counter'>Refresh to increment</a></p>", "utf-8"))
            self.wfile.write(bytes("<p><a href='/'>Back to Home</a></p>", "utf-8"))
            self.wfile.write(bytes("</body></html>", "utf-8"))
        
        else:
            # 404 for any other path
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(bytes("<html><head><title>404 Not Found</title></head>", "utf-8"))
            self.wfile.write(bytes("<body><h1>404 Not Found</h1>", "utf-8"))
            self.wfile.write(bytes("<p>The requested path was not found.</p>", "utf-8"))
            self.wfile.write(bytes("<p><a href='/'>Back to Home</a></p>", "utf-8"))
            self.wfile.write(bytes("</body></html>", "utf-8"))

def run_server(port=8000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, SimpleServer)
    print(f"Starting server on port {port}...")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()
"""

async def test_sandbox_execution():
    """Test how code execution works in the sandbox."""
    try:
        # Import the necessary modules
        from sandbox.sandbox import get_or_start_sandbox
        from daytona_sdk import SessionExecuteRequest
        
        print("\n" + "=" * 80)
        print("🧪 SANDBOX CODE EXECUTION TEST")
        print("=" * 80)
        
        # Get a sandbox instance
        # Note: This assumes a sandbox already exists with this ID
        # You'll need to replace this with a valid sandbox ID from your environment
        sandbox_id = "test_sandbox"
        try:
            sandbox = await get_or_start_sandbox(sandbox_id)
            print(f"✅ Connected to sandbox: {sandbox_id}")
        except Exception as e:
            print(f"❌ Failed to connect to sandbox: {e}")
            print("This test requires an existing sandbox. Please create one first.")
            return
        
        # Create a session for our commands
        session_id = f"test_session_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        try:
            sandbox.process.create_session(session_id)
            print(f"✅ Created session: {session_id}")
        except Exception as e:
            print(f"❌ Failed to create session: {e}")
            return
        
        # Create the web server file
        try:
            print("\n📝 Creating web server file...")
            
            # Create the file in the workspace
            file_path = "/workspace/simple_server.py"
            sandbox.fs.upload_file(file_path, SAMPLE_WEB_SERVER.encode())
            print(f"✅ Created file: {file_path}")
            
            # Make it executable
            sandbox.fs.set_file_permissions(file_path, "755")
            print("✅ Set file permissions")
        except Exception as e:
            print(f"❌ Failed to create web server file: {e}")
            return
        
        # Run the web server in the background
        try:
            print("\n🚀 Starting web server in the background...")
            
            # Execute the command in the session
            command = f"cd /workspace && python simple_server.py > server.log 2>&1 &"
            req = SessionExecuteRequest(
                command=command,
                var_async=True,
                cwd="/workspace"
            )
            
            response = sandbox.process.execute_session_command(
                session_id=session_id,
                req=req,
                timeout=5
            )
            
            print(f"✅ Started web server (command ID: {response.cmd_id})")
            
            # Wait a moment for the server to start
            print("⏳ Waiting for server to start...")
            await asyncio.sleep(2)
            
            # Check if the server is running
            ps_req = SessionExecuteRequest(
                command="ps aux | grep simple_server.py | grep -v grep",
                var_async=False,
                cwd="/workspace"
            )
            
            ps_response = sandbox.process.execute_session_command(
                session_id=session_id,
                req=ps_req,
                timeout=5
            )
            
            logs = sandbox.process.get_session_command_logs(
                session_id=session_id,
                command_id=ps_response.cmd_id
            )
            
            if ps_response.exit_code == 0:
                print(f"✅ Server is running:\n{logs}")
            else:
                print(f"❌ Server does not appear to be running")
                return
            
            # Test the server using curl
            print("\n🌐 Testing web server endpoints...")
            
            # Test root endpoint
            curl_req = SessionExecuteRequest(
                command="curl -s http://localhost:8000/",
                var_async=False,
                cwd="/workspace"
            )
            
            curl_response = sandbox.process.execute_session_command(
                session_id=session_id,
                req=curl_req,
                timeout=5
            )
            
            curl_logs = sandbox.process.get_session_command_logs(
                session_id=session_id,
                command_id=curl_response.cmd_id
            )
            
            if curl_response.exit_code == 0 and "Hello, World!" in curl_logs:
                print("✅ Root endpoint test successful")
            else:
                print(f"❌ Root endpoint test failed: {curl_logs}")
            
            # Test time endpoint
            curl_time_req = SessionExecuteRequest(
                command="curl -s http://localhost:8000/time",
                var_async=False,
                cwd="/workspace"
            )
            
            curl_time_response = sandbox.process.execute_session_command(
                session_id=session_id,
                req=curl_time_req,
                timeout=5
            )
            
            curl_time_logs = sandbox.process.get_session_command_logs(
                session_id=session_id,
                command_id=curl_time_response.cmd_id
            )
            
            if curl_time_response.exit_code == 0 and "Current Time" in curl_time_logs:
                print("✅ Time endpoint test successful")
            else:
                print(f"❌ Time endpoint test failed: {curl_time_logs}")
            
            # Test counter endpoint
            curl_counter_req = SessionExecuteRequest(
                command="curl -s http://localhost:8000/counter",
                var_async=False,
                cwd="/workspace"
            )
            
            curl_counter_response = sandbox.process.execute_session_command(
                session_id=session_id,
                req=curl_counter_req,
                timeout=5
            )
            
            curl_counter_logs = sandbox.process.get_session_command_logs(
                session_id=session_id,
                command_id=curl_counter_response.cmd_id
            )
            
            if curl_counter_response.exit_code == 0 and "Visit Counter" in curl_counter_logs:
                print("✅ Counter endpoint test successful")
            else:
                print(f"❌ Counter endpoint test failed: {curl_counter_logs}")
            
        except Exception as e:
            print(f"❌ Failed to run web server: {e}")
            return
        
        # Clean up
        try:
            print("\n🧹 Cleaning up...")
            
            # Kill the web server
            kill_req = SessionExecuteRequest(
                command="pkill -f simple_server.py",
                var_async=False,
                cwd="/workspace"
            )
            
            sandbox.process.execute_session_command(
                session_id=session_id,
                req=kill_req,
                timeout=5
            )
            
            # Delete the session
            sandbox.process.delete_session(session_id)
            
            print("✅ Cleanup complete")
        except Exception as e:
            print(f"❌ Failed to clean up: {e}")
        
        print("\n" + "=" * 80)
        print("✅ TEST COMPLETE")
        print("=" * 80)
        print("This test demonstrates how the agent executes code in the sandbox.")
        print("The agent can create files, run commands, and interact with running services.")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_sandbox_execution())
