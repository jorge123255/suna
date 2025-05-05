#!/usr/bin/env python3
"""
Script to check for installed Ollama models and pull required models if they're not already installed.
"""

import requests
import json
import time
import sys
import os
from typing import List, Dict, Any, Optional

# Configuration
OLLAMA_API_BASE = "http://192.168.1.10:11434"  # From your docker-compose.yaml
MODELS_TO_CHECK = [
    # For coding tasks
    "qwen3:14b-instruct-q4_K_M",  # Newer Qwen3 model for coding
    "qwen2.5-coder:32b-instruct-q8_0",  # Specialized coding model
    
    # For reasoning tasks
    "mixtral:8x22b-instruct-v0.1-q4_K_M",  # Powerful reasoning model
    
    # For creative tasks
    "llama3:8b",  # Good for creative tasks
    "qwen3:8b-instruct-q4_K_M",  # Newer alternative for creative tasks
    
    # For general chat
    "qwen3:32b-instruct-q4_K_M",  # Latest Qwen3 model
    "qwen2.5:32b-instruct-q4_K_M"  # Current default model
]

def get_installed_models() -> List[Dict[str, Any]]:
    """Get a list of all installed models on the Ollama server."""
    try:
        response = requests.get(f"{OLLAMA_API_BASE}/api/tags")
        if response.status_code == 200:
            return response.json().get("models", [])
        else:
            print(f"Error fetching models: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"Exception when fetching models: {e}")
        return []

def is_model_installed(model_name: str, installed_models: List[Dict[str, Any]]) -> bool:
    """Check if a specific model is installed."""
    return any(model.get("name") == model_name for model in installed_models)

def pull_model(model_name: str) -> bool:
    """Pull a model from Ollama."""
    print(f"Pulling model: {model_name}...")
    try:
        response = requests.post(
            f"{OLLAMA_API_BASE}/api/pull",
            json={"name": model_name},
            stream=True
        )
        
        if response.status_code != 200:
            print(f"Error starting model pull: {response.status_code} - {response.text}")
            return False
        
        # Process the streaming response to show progress
        for line in response.iter_lines():
            if line:
                try:
                    progress_data = json.loads(line)
                    if "status" in progress_data:
                        status = progress_data.get("status")
                        if "completed" in progress_data and progress_data.get("completed"):
                            print(f"Status: {status} - Completed!")
                        elif "total" in progress_data and "completed" in progress_data:
                            total = progress_data.get("total", 0)
                            completed = progress_data.get("completed", 0)
                            if total > 0:
                                percentage = (completed / total) * 100
                                print(f"Status: {status} - {percentage:.2f}% ({completed}/{total})")
                            else:
                                print(f"Status: {status}")
                        else:
                            print(f"Status: {status}")
                except json.JSONDecodeError:
                    print(f"Could not parse progress data: {line}")
        
        print(f"Successfully pulled model: {model_name}")
        return True
    except Exception as e:
        print(f"Exception when pulling model {model_name}: {e}")
        return False

def update_task_classifier(models_to_use: Dict[str, str]) -> None:
    """Update the task classifier with the models we've installed."""
    task_classifier_path = "/Volumes/appdata/suna/backend/services/task_classifier.py"
    embedding_classifier_path = "/Volumes/appdata/suna/backend/services/embedding_task_classifier.py"
    
    for file_path in [task_classifier_path, embedding_classifier_path]:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Find the TASK_MODELS dictionary
            start_idx = content.find("TASK_MODELS = {")
            if start_idx != -1:
                end_idx = content.find("}", start_idx)
                if end_idx != -1:
                    # Create the new dictionary content
                    new_dict_content = "TASK_MODELS = {\n"
                    for task, model in models_to_use.items():
                        new_dict_content += f'    "{task}": "{model}",\n'
                    new_dict_content += "}"
                    
                    # Replace the old dictionary with the new one
                    new_content = content[:start_idx] + new_dict_content + content[end_idx+1:]
                    
                    with open(file_path, 'w') as f:
                        f.write(new_content)
                    
                    print(f"Updated {file_path} with new model mappings")

def main():
    """Main function to check and pull models."""
    print(f"Checking for installed models on {OLLAMA_API_BASE}...")
    
    installed_models = get_installed_models()
    if not installed_models:
        print("Could not fetch installed models. Please check if the Ollama server is running.")
        sys.exit(1)
    
    print("\nCurrently installed models:")
    for model in installed_models:
        print(f"- {model.get('name')} ({model.get('size', 'unknown size')})")
    
    print("\nChecking for required models...")
    models_to_pull = []
    for model_name in MODELS_TO_CHECK:
        if is_model_installed(model_name, installed_models):
            print(f"✓ {model_name} is already installed")
        else:
            print(f"✗ {model_name} is not installed")
            models_to_pull.append(model_name)
    
    if not models_to_pull:
        print("\nAll required models are already installed!")
    else:
        print(f"\nNeed to pull {len(models_to_pull)} models:")
        for model_name in models_to_pull:
            print(f"- {model_name}")
        
        print("\nStarting model pulls...")
        for model_name in models_to_pull:
            success = pull_model(model_name)
            if not success:
                print(f"Failed to pull {model_name}")
    
    # Determine which models to use based on what's installed
    models_to_use = {
        "coding": None,
        "reasoning": None,
        "creative": None,
        "general": None
    }
    
    # Check for coding models
    if is_model_installed("qwen3:14b-instruct-q4_K_M", installed_models):
        models_to_use["coding"] = "qwen3:14b-instruct-q4_K_M"
    elif is_model_installed("qwen2.5-coder:32b-instruct-q8_0", installed_models):
        models_to_use["coding"] = "qwen2.5-coder:32b-instruct-q8_0"
    
    # Check for reasoning models
    if is_model_installed("mixtral:8x22b-instruct-v0.1-q4_K_M", installed_models):
        models_to_use["reasoning"] = "mixtral:8x22b-instruct-v0.1-q4_K_M"
    
    # Check for creative models
    if is_model_installed("qwen3:8b-instruct-q4_K_M", installed_models):
        models_to_use["creative"] = "qwen3:8b-instruct-q4_K_M"
    elif is_model_installed("llama3:8b", installed_models):
        models_to_use["creative"] = "llama3:8b"
    
    # Check for general chat models
    if is_model_installed("qwen3:32b-instruct-q4_K_M", installed_models):
        models_to_use["general"] = "qwen3:32b-instruct-q4_K_M"
    elif is_model_installed("qwen2.5:32b-instruct-q4_K_M", installed_models):
        models_to_use["general"] = "qwen2.5:32b-instruct-q4_K_M"
    
    # Fill in any missing models with defaults
    for task, model in models_to_use.items():
        if model is None:
            # Find any installed model to use as fallback
            for check_model in MODELS_TO_CHECK:
                if is_model_installed(check_model, installed_models):
                    models_to_use[task] = check_model
                    break
    
    print("\nModels selected for each task type:")
    for task, model in models_to_use.items():
        print(f"- {task}: {model}")
    
    # Update the task classifier with the models we've selected
    update_task_classifier(models_to_use)
    
    print("\nDone!")

if __name__ == "__main__":
    main()
