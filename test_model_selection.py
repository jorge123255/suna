#!/usr/bin/env python3
"""
Test script for the automatic model selection feature.
This script will test various prompts and show which model would be selected for each.
"""

import sys
import os
import requests
import json
from typing import Dict, Any, List

# Add the backend directory to the path so we can import the services
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Import the task classifier
try:
    from services.embedding_task_classifier import get_model_for_task, classify_task_with_embeddings
    from utils.logger import logger
    import logging
    
    # Set logger to INFO level
    logger.setLevel(logging.INFO)
    
    # Add a console handler if not already present
    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running this script from the root directory of the project.")
    sys.exit(1)

# Test prompts for different task types
TEST_PROMPTS = {
    "coding": [
        "Can you help me debug this Python function that's giving me an IndexError?",
        "Write a React component that implements a dropdown menu with search functionality",
        "How do I optimize this SQL query that's taking too long to execute?",
        "Explain the difference between promises and async/await in JavaScript",
        "Help me set up Docker Compose for my MERN stack application"
    ],
    "reasoning": [
        "What are the ethical considerations of using AI in healthcare decision making?",
        "Compare the pros and cons of microservices versus monolithic architecture for a banking system",
        "Analyze the potential long-term economic impacts of universal basic income",
        "What are the logical fallacies in this argument about climate change?",
        "Develop a framework for evaluating the success of a remote work policy"
    ],
    "creative": [
        "Write a short story about a robot that develops consciousness",
        "Create a marketing campaign for a new eco-friendly product",
        "Design a character for a science fiction novel set 200 years in the future",
        "Write a poem about the changing seasons",
        "Come up with a unique restaurant concept that hasn't been done before"
    ],
    "general": [
        "What's the weather like in New York today?",
        "Who won the World Cup in 2022?",
        "How do I make sourdough bread?",
        "What are some good exercises for lower back pain?",
        "Tell me about the history of the Roman Empire"
    ],
    "mixed": [
        "Can you write a Python script that analyzes sentiment in tweets about climate change?",
        "Design a database schema for a hospital management system and explain the ethical implications",
        "Write a creative story about a programmer who discovers a bug that changes reality",
        "What's the best way to learn machine learning? Can you create a study plan and write a motivational poem?",
        "Compare different sorting algorithms and explain which one would be best for sorting a large dataset of patient records"
    ]
}

def test_model_selection():
    """Test the model selection for various prompts."""
    print("\n===== AUTOMATIC MODEL SELECTION TEST =====\n")
    
    results = {}
    
    for category, prompts in TEST_PROMPTS.items():
        print(f"\n----- Testing {category.upper()} prompts -----\n")
        category_results = []
        
        for i, prompt in enumerate(prompts):
            print(f"Prompt {i+1}: {prompt}")
            
            try:
                # Get the task type and confidence
                task_type, confidence = classify_task_with_embeddings(prompt)
                
                # Get the model
                model = get_model_for_task(prompt)
                
                result = {
                    "prompt": prompt,
                    "classified_as": task_type,
                    "confidence": f"{confidence:.2f}",
                    "selected_model": model
                }
                
                print(f"  Classified as: {task_type}")
                print(f"  Confidence: {confidence:.2f}")
                print(f"  Selected model: {model}")
                print()
                
                category_results.append(result)
            except Exception as e:
                print(f"  Error: {e}")
                print()
        
        results[category] = category_results
    
    # Save results to a file
    with open("model_selection_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\nResults saved to model_selection_results.json")
    print("\n===== TEST COMPLETED =====\n")

if __name__ == "__main__":
    test_model_selection()
