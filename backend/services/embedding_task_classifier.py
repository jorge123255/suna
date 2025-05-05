"""
Embedding-based task classifier for determining the appropriate model for a given task.
"""

import numpy as np
from typing import Dict, Any, Tuple, List, Optional
import os
import json
import requests
from utils.logger import logger
from utils.config import config

# Task types and their corresponding models
TASK_MODELS = {
    "coding": "qwen2.5-coder:32b-instruct-q8_0",     # Specialized coding model
    "reasoning": "mixtral:8x22b-instruct-v0.1-q4_K_M", # Powerful reasoning model
    "creative": "qwen3:8b",                         # Qwen3 for creative tasks
    "general": "qwen3:32b"                          # Qwen3 for general tasks
}

# Example prompts for each task type
TASK_EXAMPLES = {
    "coding": [
        "Can you help me debug this Python code?",
        "Write a function to calculate Fibonacci numbers",
        "How do I implement a binary search tree in JavaScript?",
        "What's the best way to optimize this SQL query?",
        "Create a React component for a login form",
        "Help me understand this error in my code",
        "How do I use async/await in JavaScript?",
        "Write a unit test for this function",
        "Explain the difference between inheritance and composition",
        "How do I connect to a MongoDB database in Node.js?",
        "Refactor this code to follow clean code principles",
        "Create a CI/CD pipeline for my project",
        "Implement a RESTful API for user authentication",
        "How do I use Docker to containerize my application?",
        "Write a regex pattern to validate email addresses"
    ],
    "reasoning": [
        "What are the pros and cons of remote work?",
        "Analyze the impact of AI on the job market",
        "Compare and contrast microservices vs monolithic architecture",
        "What are the ethical implications of facial recognition technology?",
        "Explain the concept of diminishing returns",
        "What factors should I consider when making this business decision?",
        "Analyze this research paper and explain its key findings",
        "What are the logical fallacies in this argument?",
        "How might climate change affect global food security?",
        "What are the trade-offs between privacy and security in technology?",
        "Evaluate different approaches to solving this complex problem",
        "What are the second-order effects of this policy change?",
        "Develop a framework for ethical decision-making in AI",
        "How would you approach this system design challenge?",
        "What are the implications of quantum computing for cryptography?"
    ],
    "creative": [
        "Write a short story about a time traveler",
        "Create a poem about the ocean",
        "Imagine a world where humans can fly",
        "Design a character for a fantasy novel",
        "Come up with a unique restaurant concept",
        "Write a dialogue between two historical figures",
        "Create a marketing slogan for a new eco-friendly product",
        "Describe an alien civilization unlike anything on Earth",
        "Write a song about overcoming adversity",
        "Design a game concept with unique mechanics",
        "Create an alternative history scenario",
        "Write a compelling elevator pitch for a startup",
        "Design a futuristic transportation system",
        "Create a new mythological creature and its backstory",
        "Write a scene that evokes a specific emotion"
    ],
    "general": [
        "What's the weather like today?",
        "How do I make pasta?",
        "Tell me about the history of Rome",
        "What movies are playing this weekend?",
        "How tall is Mount Everest?",
        "What's the capital of Australia?",
        "How do I change a flat tire?",
        "What are some good books to read?",
        "Tell me about quantum physics",
        "What's the difference between alligators and crocodiles?",
        "What are the symptoms of the common cold?",
        "How do I improve my public speaking skills?",
        "What's the best way to learn a new language?",
        "Tell me about the major events of World War II",
        "What are some healthy breakfast options?"
    ]
}

# Cache for embeddings to avoid recomputing
EMBEDDING_CACHE = {}
TASK_EMBEDDINGS = {}

def cosine_similarity(a: List[float], b: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        a: First vector
        b: Second vector
        
    Returns:
        Cosine similarity (between -1 and 1)
    """
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def get_embedding(text: str) -> List[float]:
    """
    Get embedding for a text using a local model or external API.
    
    Args:
        text: Text to get embedding for
        
    Returns:
        Embedding vector
    """
    # Check cache first
    if text in EMBEDDING_CACHE:
        return EMBEDDING_CACHE[text]
    
    try:
        # Option 1: Use Ollama for embeddings (if available)
        try:
            # Use the Ollama API base from config or default to localhost
            ollama_api_base = os.environ.get("OLLAMA_API_BASE", "http://localhost:11434")
            response = requests.post(
                f"{ollama_api_base}/api/embeddings",
                json={"model": "mxbai-embed-large:latest", "prompt": text}
            )
            if response.status_code == 200:
                embedding = response.json().get("embedding", [])
                EMBEDDING_CACHE[text] = embedding
                return embedding
        except Exception as e:
            logger.warning(f"Failed to get embedding from Ollama: {e}")
        
        # Option 2: Use OpenAI's embeddings API (if configured)
        if config.OPENAI_API_KEY:
            import openai
            openai.api_key = config.OPENAI_API_KEY
            
            response = openai.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            embedding = response.data[0].embedding
            EMBEDDING_CACHE[text] = embedding
            return embedding
            
        # Option 3: Use a simple fallback method if no embedding service is available
        # This is not ideal but better than failing completely
        words = text.lower().split()
        # Create a very simple embedding (word count based)
        simple_embedding = [0.0] * 100  # 100-dimensional space
        for i, word in enumerate(words[:100]):
            # Hash the word to get a consistent position
            position = hash(word) % 100
            simple_embedding[position] += 1.0 / (i + 1)  # Weight by position
            
        # Normalize
        norm = np.linalg.norm(simple_embedding)
        if norm > 0:
            simple_embedding = [x / norm for x in simple_embedding]
            
        EMBEDDING_CACHE[text] = simple_embedding
        return simple_embedding
            
    except Exception as e:
        logger.error(f"Error getting embedding: {e}")
        # Return a zero vector as fallback
        return [0.0] * 100

def initialize_task_embeddings():
    """
    Initialize task embeddings by averaging example embeddings.
    """
    global TASK_EMBEDDINGS
    
    # Skip if already initialized
    if TASK_EMBEDDINGS:
        return
        
    for task_type, examples in TASK_EXAMPLES.items():
        # Get embeddings for all examples
        embeddings = [get_embedding(example) for example in examples]
        
        # Average the embeddings
        if embeddings:
            avg_embedding = np.mean(embeddings, axis=0).tolist()
            TASK_EMBEDDINGS[task_type] = avg_embedding
            logger.info(f"Initialized embedding for task type: {task_type}")

def classify_task_with_embeddings(prompt: str) -> Tuple[str, float]:
    """
    Classify a task based on the prompt using embeddings.
    
    Args:
        prompt: The user's prompt
        
    Returns:
        A tuple of (task_type, confidence)
    """
    # Initialize task embeddings if not already done
    if not TASK_EMBEDDINGS:
        initialize_task_embeddings()
    
    # Get embedding for the prompt
    prompt_embedding = get_embedding(prompt)
    
    # Calculate similarity with each task type
    similarities = {}
    for task_type, task_embedding in TASK_EMBEDDINGS.items():
        similarity = cosine_similarity(prompt_embedding, task_embedding)
        similarities[task_type] = similarity
    
    logger.debug(f"Task similarities: {similarities}")
    
    # Sort task types by similarity
    sorted_similarities = sorted(similarities.items(), key=lambda x: x[1], reverse=True)
    best_task_type, max_similarity = sorted_similarities[0]
    
    # Define confidence thresholds for different task types
    # These thresholds determine how confident we need to be to classify a task
    confidence_thresholds = {
        "coding": 0.65,      # Higher threshold for coding tasks
        "reasoning": 0.60,  # Slightly lower for reasoning tasks
        "creative": 0.65,   # Higher for creative tasks
        "general": 0.50     # Lower threshold for general tasks
    }
    
    # Convert similarity (-1 to 1) to confidence (0 to 1)
    confidence = (max_similarity + 1) / 2
    
    # If the confidence is below the threshold for the best task type,
    # check if there's a significant gap between the top two task types
    if len(sorted_similarities) > 1 and confidence < confidence_thresholds[best_task_type]:
        second_best_type, second_similarity = sorted_similarities[1]
        second_confidence = (second_similarity + 1) / 2
        
        # If the gap is small, and the second best is "general", use that instead
        # This helps prevent misclassification when the prompt is ambiguous
        confidence_gap = confidence - second_confidence
        if confidence_gap < 0.1 and second_best_type == "general":
            best_task_type = "general"
            confidence = second_confidence
            logger.info(f"Reclassified ambiguous task as general due to small confidence gap")
    
    # If the confidence is still very low, default to general
    if confidence < 0.55:
        logger.info(f"Low confidence ({confidence:.2f}) for {best_task_type}, defaulting to general")
        best_task_type = "general"
    
    logger.info(f"Classified task as {best_task_type} with confidence {confidence:.2f}")
    return best_task_type, confidence

def get_model_for_task(prompt: str) -> str:
    """
    Get the appropriate model for a given task using embedding-based classification.
    
    Args:
        prompt: The user's prompt
        
    Returns:
        The name of the model to use
    """
    # Import the logger here to avoid circular imports
    try:
        from services.model_selection_logger import log_model_selection
    except ImportError:
        # If the logger module isn't available, create a dummy function
        def log_model_selection(*args, **kwargs):
            pass
    
    task_type, confidence = classify_task_with_embeddings(prompt)
    
    # Get the model for the task type
    model = TASK_MODELS.get(task_type, TASK_MODELS["general"])
    override_reason = None
    
    # For complex prompts that might involve multiple task types,
    # we can make more nuanced decisions
    prompt_lower = prompt.lower()
    
    # Check for specific indicators that might override the classification
    if task_type != "coding" and any(term in prompt_lower for term in [
        "code", "function", "programming", "debug", "algorithm", "class", 
        "method", "variable", "compile", "syntax", "api"]):
        # This looks like it might involve coding despite classification
        override_reason = "coding_keywords_detected"
        logger.info(f"Overriding classification to coding based on keywords")
        model = TASK_MODELS["coding"]
    
    # For very long or complex prompts, prefer more powerful models
    elif len(prompt.split()) > 100 and task_type != "reasoning":
        override_reason = "long_complex_prompt"
        logger.info(f"Long complex prompt detected, using reasoning model")
        model = TASK_MODELS["reasoning"]
    
    # For prompts that explicitly mention reasoning or analysis
    elif task_type != "reasoning" and any(term in prompt_lower for term in [
        "analyze", "evaluate", "compare", "contrast", "implications", 
        "reasoning", "logic", "argument", "debate", "philosophy"]):
        override_reason = "reasoning_terms_detected"
        logger.info(f"Reasoning terms detected, using reasoning model")
        model = TASK_MODELS["reasoning"]
    
    logger.info(f"Selected model {model} for task type {task_type}")
    
    # Log the model selection for analysis
    log_model_selection(
        prompt=prompt,
        task_type=task_type,
        confidence=confidence,
        selected_model=model,
        override_reason=override_reason
    )
    
    return model

def save_embeddings_cache(file_path: str = "embedding_cache.json"):
    """
    Save the embedding cache to a file.
    
    Args:
        file_path: Path to save the cache to
    """
    try:
        with open(file_path, "w") as f:
            json.dump(EMBEDDING_CACHE, f)
        logger.info(f"Saved embedding cache to {file_path}")
    except Exception as e:
        logger.error(f"Failed to save embedding cache: {e}")

def load_embeddings_cache(file_path: str = "embedding_cache.json"):
    """
    Load the embedding cache from a file.
    
    Args:
        file_path: Path to load the cache from
    """
    global EMBEDDING_CACHE
    
    try:
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                EMBEDDING_CACHE = json.load(f)
            logger.info(f"Loaded embedding cache from {file_path} with {len(EMBEDDING_CACHE)} entries")
    except Exception as e:
        logger.error(f"Failed to load embedding cache: {e}")

def get_available_task_models() -> List[Dict[str, Any]]:
    """
    Get a list of available task-specific models.
    
    Returns:
        A list of model information
    """
    return [
        {
            "task_type": task_type,
            "model_name": model_name,
            "description": f"Optimized for {task_type} tasks"
        }
        for task_type, model_name in TASK_MODELS.items()
    ]

# Initialize embeddings when module is loaded
try:
    initialize_task_embeddings()
except Exception as e:
    logger.error(f"Failed to initialize task embeddings: {e}")
