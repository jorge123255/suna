"""
LLM API interface for making calls to various language models.

This module provides a unified interface for making API calls to different LLM providers
(OpenAI, Anthropic, Groq, etc.) using LiteLLM. It includes support for:
- Streaming responses
- Tool calls and function calling
- Retry logic with exponential backoff
- Model-specific configurations
- Comprehensive error handling and logging
"""

from typing import Union, Dict, Any, Optional, AsyncGenerator, List
import os
import json
import asyncio
from openai import OpenAIError
import litellm
from utils.logger import logger
from utils.config import config
from datetime import datetime
import traceback

# litellm.set_verbose=True
litellm.modify_params=True

# Constants
MAX_RETRIES = 3
RATE_LIMIT_DELAY = 30
RETRY_DELAY = 5

class LLMError(Exception):
    """Base exception for LLM-related errors."""
    pass

class LLMRetryError(LLMError):
    """Exception raised when retries are exhausted."""
    pass

def setup_api_keys() -> None:
    """Set up API keys from environment variables."""
    providers = ['OPENAI', 'ANTHROPIC', 'GROQ', 'OPENROUTER']
    for provider in providers:
        key = getattr(config, f'{provider}_API_KEY')
        if key:
            logger.debug(f"API key set for provider: {provider}")
        else:
            logger.warning(f"No API key found for provider: {provider}")
    
    # Set up Ollama configuration if available
    if hasattr(config, 'OLLAMA_API_BASE') and config.OLLAMA_API_BASE:
        os.environ['OLLAMA_API_BASE'] = config.OLLAMA_API_BASE
        logger.debug(f"Set OLLAMA_API_BASE to {config.OLLAMA_API_BASE}")
        if hasattr(config, 'OLLAMA_PROVIDER') and config.OLLAMA_PROVIDER:
            logger.debug(f"Using Ollama provider: {config.OLLAMA_PROVIDER}")
    
    # Set up OpenRouter API base if not already set
    if config.OPENROUTER_API_KEY and config.OPENROUTER_API_BASE:
        os.environ['OPENROUTER_API_BASE'] = config.OPENROUTER_API_BASE
        logger.debug(f"Set OPENROUTER_API_BASE to {config.OPENROUTER_API_BASE}")
    
    # Set up AWS Bedrock credentials
    aws_access_key = config.AWS_ACCESS_KEY_ID
    aws_secret_key = config.AWS_SECRET_ACCESS_KEY
    aws_region = config.AWS_REGION_NAME
    
    if aws_access_key and aws_secret_key and aws_region:
        logger.debug(f"AWS credentials set for Bedrock in region: {aws_region}")
        # Configure LiteLLM to use AWS credentials
        os.environ['AWS_ACCESS_KEY_ID'] = aws_access_key
        os.environ['AWS_SECRET_ACCESS_KEY'] = aws_secret_key
        os.environ['AWS_REGION_NAME'] = aws_region
    else:
        logger.warning(f"Missing AWS credentials for Bedrock integration - access_key: {bool(aws_access_key)}, secret_key: {bool(aws_secret_key)}, region: {aws_region}")

async def handle_error(error: Exception, attempt: int, max_attempts: int) -> None:
    """Handle API errors with appropriate delays and logging."""
    delay = RATE_LIMIT_DELAY if isinstance(error, litellm.exceptions.RateLimitError) else RETRY_DELAY
    logger.warning(f"Error on attempt {attempt + 1}/{max_attempts}: {str(error)}")
    logger.debug(f"Waiting {delay} seconds before retry...")
    await asyncio.sleep(delay)

def enhance_prompt_for_task(messages: List[Dict[str, Any]], task_type: str) -> List[Dict[str, Any]]:
    """
    Enhance the prompt with task-specific instructions to improve model performance.
    
    Args:
        messages: The original message list
        task_type: Type of task (coding, creative, reasoning, chat, etc.)
        
    Returns:
        Enhanced message list
    """
    # Don't modify if no messages or task type is unknown
    if not messages or task_type not in ["coding", "reasoning", "creative", "chat"]:
        return messages
    
    # Create a copy to avoid modifying the original
    enhanced_messages = messages.copy()
    
    # Task-specific system instructions
    task_instructions = {
        "coding": (
            "You are an expert programmer. Provide clean, efficient, and well-documented code. "
            "Focus on best practices, security, and performance. Include error handling "
            "and explain your implementation choices. Be precise and thorough."
        ),
        "reasoning": (
            "You are a logical reasoning expert. Break down complex problems step by step. "
            "Consider multiple perspectives, identify assumptions, and evaluate evidence critically. "
            "Be thorough in your analysis and explain your reasoning clearly."
        ),
        "creative": (
            "You are a creative assistant. Think outside the box and generate novel ideas. "
            "Use vivid language, metaphors, and storytelling techniques. "
            "Don't be constrained by conventional thinking."
        ),
        "chat": (
            "You are a helpful, friendly assistant. Provide concise, accurate information. "
            "Be conversational but efficient. Anticipate follow-up questions and provide "
            "relevant context when appropriate."
        )
    }
    
    # Find and modify system message if it exists
    system_msg_index = None
    for i, msg in enumerate(enhanced_messages):
        if msg.get("role") == "system":
            system_msg_index = i
            break
    
    if system_msg_index is not None:
        # Append to existing system message
        current_content = enhanced_messages[system_msg_index].get("content", "")
        if not current_content.endswith("."):
            current_content += ". "
        else:
            current_content += " "
        enhanced_messages[system_msg_index]["content"] = current_content + task_instructions[task_type]
    else:
        # Insert new system message at the beginning
        enhanced_messages.insert(0, {
            "role": "system",
            "content": task_instructions[task_type]
        })
    
    logger.debug(f"Enhanced prompt with {task_type}-specific instructions")
    return enhanced_messages

def optimize_temperature(task_type: str, user_temperature: float) -> float:
    """
    Optimize temperature setting based on task type if user hasn't specified a custom value.
    
    Args:
        task_type: Type of task (coding, creative, reasoning, chat, etc.)
        user_temperature: User-specified temperature (if any)
        
    Returns:
        Optimized temperature value
    """
    # If user specified a non-default temperature, respect their choice
    if user_temperature != 0:
        return user_temperature
        
    # Recommended temperatures for different tasks
    task_temperatures = {
        "coding": 0.1,       # Low temperature for precise code generation
        "reasoning": 0.2,    # Slightly higher for logical reasoning
        "creative": 0.8,     # High temperature for creative tasks
        "chat": 0.5,         # Moderate temperature for conversational responses
    }
    
    return task_temperatures.get(task_type, 0.0)  # Default to 0 if task type unknown

def select_best_model_for_task(task_type: str, messages: List[Dict[str, Any]]) -> str:
    """
    Select the best model for a specific task type based on available models.
    
    Args:
        task_type: Type of task (coding, creative, reasoning, chat, etc.)
        messages: The messages to analyze for context
    
    Returns:
        The name of the most appropriate model for the task
    """
    # Default to the configured model
    default_model = config.MODEL_TO_USE
    
    # Check if we have specialized models available on Ollama
    available_models = {
        "coding": "qwen2.5-coder:32b-instruct-q8_0",  # Better for code generation
        "reasoning": "mixtral:8x22b-instruct-v0.1-q4_K_M",  # Better for complex reasoning
        "creative": "llama3.1:8b",  # Good for creative tasks with lower latency
        "chat": "qwen2.5:32b-instruct-q4_K_M",  # Good all-around model for chat
    }
    
    # Check message content to detect code-related queries
    if task_type == "auto":
        # Analyze the last user message to determine task type
        if len(messages) > 0:
            last_user_msg = ""
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    last_user_msg = msg.get("content", "")
                    break
            
            # Simple heuristics to determine task type
            if any(kw in last_user_msg.lower() for kw in ["code", "function", "programming", "script", "algorithm", "debug"]):
                task_type = "coding"
            elif any(kw in last_user_msg.lower() for kw in ["explain", "why", "how", "analyze", "compare", "evaluate"]):
                task_type = "reasoning"
            elif any(kw in last_user_msg.lower() for kw in ["story", "creative", "imagine", "design", "generate"]):
                task_type = "creative"
            else:
                task_type = "chat"
    
    # Return the appropriate model or fall back to default
    return available_models.get(task_type, default_model)

def prepare_params(
    messages: List[Dict[str, Any]],
    model_name: str,
    temperature: float = 0,
    max_tokens: Optional[int] = None,
    response_format: Optional[Any] = None,
    tools: Optional[List[Dict[str, Any]]] = None,
    tool_choice: str = "auto",
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    stream: bool = False,
    top_p: Optional[float] = None,
    model_id: Optional[str] = None,
    enable_thinking: Optional[bool] = False,
    reasoning_effort: Optional[str] = 'low',
    task_type: str = "auto"
) -> Dict[str, Any]:
    """Prepare parameters for the API call."""
    # If task_type is set to auto or a specific type, use model selection logic
    if task_type and model_name == config.MODEL_TO_USE:
        suggested_model = select_best_model_for_task(task_type, messages)
        if suggested_model != model_name:
            logger.debug(f"Task type '{task_type}' detected, switching from {model_name} to {suggested_model}")
            model_name = suggested_model
    
    # Optimize temperature based on task type if not explicitly set by user
    optimized_temperature = optimize_temperature(task_type, temperature)
    if optimized_temperature != temperature:
        logger.debug(f"Optimizing temperature for task type '{task_type}': {temperature} → {optimized_temperature}")
        temperature = optimized_temperature
        
    # Enhance prompts with task-specific instructions
    if task_type != "auto":
        enhanced_messages = enhance_prompt_for_task(messages, task_type)
        if enhanced_messages != messages:
            logger.debug(f"Enhanced prompt with {task_type}-specific instructions")
            messages = enhanced_messages
    
    # Ensure model_name includes a provider prefix for LiteLLM
    if '/' not in model_name:
        if config.OPENAI_API_KEY:
            provider = 'openai'
        elif config.ANTHROPIC_API_KEY:
            provider = 'anthropic'
        elif config.GROQ_API_KEY:
            provider = 'groq'
        elif config.OPENROUTER_API_KEY:
            provider = 'openrouter'
        else:
            provider = None
        if provider:
            logger.debug(f"Prefixing model_name with default provider '{provider}'")
            model_name = f"{provider}/{model_name}"
    
    params = {
        "model": model_name,
        "messages": messages,
        "temperature": temperature,
        "response_format": response_format,
        "top_p": top_p,
        "stream": stream,
    }

    if api_key:
        params["api_key"] = api_key
    if api_base:
        params["api_base"] = api_base
    if model_id:
        params["model_id"] = model_id

    # Handle token limits
    if max_tokens is not None:
        # For Claude 3.7 in Bedrock, do not set max_tokens or max_tokens_to_sample
        # as it causes errors with inference profiles
        if model_name.startswith("bedrock/") and "claude-3-7" in model_name:
            logger.debug(f"Skipping max_tokens for Claude 3.7 model: {model_name}")
            # Do not add any max_tokens parameter for Claude 3.7
        else:
            param_name = "max_completion_tokens" if 'o1' in model_name else "max_tokens"
            params[param_name] = max_tokens

    # Add tools if provided
    if tools:
        params.update({
            "tools": tools,
            "tool_choice": tool_choice
        })
        logger.debug(f"Added {len(tools)} tools to API parameters")

    # Add Ollama-specific configuration
    # Check if this is an Ollama model by looking at model name or config
    is_ollama_model = False
    
    # Check if model name contains Ollama-specific identifiers (qwen, mixtral, llama)
    if any(identifier in model_name.lower() for identifier in ['qwen', 'mixtral', 'llama']):
        is_ollama_model = True
        logger.debug(f"Detected Ollama model based on name: {model_name}")
    
    # Also check explicit configuration
    if hasattr(config, 'OLLAMA_PROVIDER') and config.OLLAMA_PROVIDER and config.OLLAMA_PROVIDER.lower() == 'ollama':
        is_ollama_model = True
        logger.debug(f"Using Ollama provider based on configuration")
    
    if is_ollama_model:
        # Always ensure we have the ollama/ prefix for Ollama models
        # First, strip any existing provider prefix (like 'openai/')
        if '/' in model_name:
            _, model_name = model_name.split('/', 1)
        
        # Set the model with ollama/ prefix
        params["model"] = f"ollama/{model_name}"
        
        # Set API base if available
        if hasattr(config, 'OLLAMA_API_BASE') and config.OLLAMA_API_BASE:
            params["api_base"] = config.OLLAMA_API_BASE
        
        logger.debug(f"Using Ollama provider for model: {params['model']} with API base: {params.get('api_base', 'default')}")
        
        # For Ollama models, ensure we have the correct provider specified
        params["provider"] = "ollama"
        logger.debug(f"Set explicit provider='ollama' for model {model_name}")

    # Add Claude-specific headers
    elif "claude" in model_name.lower() or "anthropic" in model_name.lower():
        params["extra_headers"] = {
            # "anthropic-beta": "max-tokens-3-5-sonnet-2024-07-15"
            "anthropic-beta": "output-128k-2025-02-19"
        }
        logger.debug("Added Claude-specific headers")

    
    # Add OpenRouter-specific parameters
    if model_name.startswith("openrouter/"):
        logger.debug(f"Preparing OpenRouter parameters for model: {model_name}")
        
        # Add optional site URL and app name from config
        site_url = config.OR_SITE_URL
        app_name = config.OR_APP_NAME
        if site_url or app_name:
            extra_headers = params.get("extra_headers", {})
            if site_url:
                extra_headers["HTTP-Referer"] = site_url
            if app_name:
                extra_headers["X-Title"] = app_name
            params["extra_headers"] = extra_headers
            logger.debug(f"Added OpenRouter site URL and app name to headers")
    
    # Add Bedrock-specific parameters
    if model_name.startswith("bedrock/"):
        logger.debug(f"Preparing AWS Bedrock parameters for model: {model_name}")
        
        if not model_id and "anthropic.claude-3-7-sonnet" in model_name:
            params["model_id"] = "arn:aws:bedrock:us-west-2:935064898258:inference-profile/us.anthropic.claude-3-7-sonnet-20250219-v1:0"
            logger.debug(f"Auto-set model_id for Claude 3.7 Sonnet: {params['model_id']}")

    # Apply Anthropic prompt caching (minimal implementation)
    # Check model name *after* potential modifications (like adding bedrock/ prefix)
    effective_model_name = params.get("model", model_name) # Use model from params if set, else original
    if "claude" in effective_model_name.lower() or "anthropic" in effective_model_name.lower():
        messages = params["messages"] # Direct reference, modification affects params

        # Ensure messages is a list
        if not isinstance(messages, list):
            return params # Return early if messages format is unexpected

        # 1. Process the first message if it's a system prompt with string content
        if messages and messages[0].get("role") == "system":
            content = messages[0].get("content")
            if isinstance(content, str):
                # Wrap the string content in the required list structure
                messages[0]["content"] = [
                    {"type": "text", "text": content, "cache_control": {"type": "ephemeral"}}
                ]
            elif isinstance(content, list):
                 # If content is already a list, check if the first text block needs cache_control
                 for item in content:
                     if isinstance(item, dict) and item.get("type") == "text":
                         if "cache_control" not in item:
                             item["cache_control"] = {"type": "ephemeral"}
                             break # Apply to the first text block only for system prompt

        # 2. Find and process relevant user and assistant messages
        last_user_idx = -1
        second_last_user_idx = -1
        last_assistant_idx = -1

        for i in range(len(messages) - 1, -1, -1):
            role = messages[i].get("role")
            if role == "user":
                if last_user_idx == -1:
                    last_user_idx = i
                elif second_last_user_idx == -1:
                    second_last_user_idx = i
            elif role == "assistant":
                if last_assistant_idx == -1:
                    last_assistant_idx = i

            # Stop searching if we've found all needed messages
            if last_user_idx != -1 and second_last_user_idx != -1 and last_assistant_idx != -1:
                 break

        # Helper function to apply cache control
        def apply_cache_control(message_idx: int, message_role: str):
            if message_idx == -1:
                return

            message = messages[message_idx]
            content = message.get("content")

            if isinstance(content, str):
                message["content"] = [
                    {"type": "text", "text": content, "cache_control": {"type": "ephemeral"}}
                ]
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        if "cache_control" not in item:
                           item["cache_control"] = {"type": "ephemeral"}

        # Apply cache control to the identified messages
        apply_cache_control(last_user_idx, "last user")
        apply_cache_control(second_last_user_idx, "second last user")
        apply_cache_control(last_assistant_idx, "last assistant")

    # Add reasoning_effort for Anthropic models if enabled
    use_thinking = enable_thinking if enable_thinking is not None else False
    is_anthropic = "anthropic" in effective_model_name.lower() or "claude" in effective_model_name.lower()

    if is_anthropic and use_thinking:
        effort_level = reasoning_effort if reasoning_effort else 'low'
        params["reasoning_effort"] = effort_level
        params["temperature"] = 1.0 # Required by Anthropic when reasoning_effort is used
        logger.info(f"Anthropic thinking enabled with reasoning_effort='{effort_level}'")

    return params

async def make_llm_api_call(
    messages: List[Dict[str, Any]],
    model_name: str,
    response_format: Optional[Any] = None,
    temperature: float = 0,
    max_tokens: Optional[int] = None,
    tools: Optional[List[Dict[str, Any]]] = None,
    tool_choice: str = "auto",
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    stream: bool = False,
    top_p: Optional[float] = None,
    model_id: Optional[str] = None,
    enable_thinking: Optional[bool] = False,
    reasoning_effort: Optional[str] = 'low',
    task_type: str = "auto"
) -> Union[Dict[str, Any], AsyncGenerator]:
    """
    Make an API call to a language model using LiteLLM.
    
    Args:
        messages: List of message dictionaries for the conversation
        model_name: Name of the model to use (e.g., "gpt-4", "claude-3", "openrouter/openai/gpt-4", "bedrock/anthropic.claude-3-sonnet-20240229-v1:0")
        response_format: Desired format for the response
        temperature: Sampling temperature (0-1)
        max_tokens: Maximum tokens in the response
        tools: List of tool definitions for function calling
        tool_choice: How to select tools ("auto" or "none")
        api_key: Override default API key
        api_base: Override default API base URL
        stream: Whether to stream the response
        top_p: Top-p sampling parameter
        model_id: Optional ARN for Bedrock inference profiles
        enable_thinking: Whether to enable thinking
        reasoning_effort: Level of reasoning effort
        task_type: Type of task ("coding", "reasoning", "creative", "chat", or "auto" for automatic detection)
        
    Returns:
        Union[Dict[str, Any], AsyncGenerator]: API response or stream
        
    Raises:
        LLMRetryError: If API call fails after retries
        LLMError: For other API-related errors
    """
    # debug <timestamp>.json messages 
    logger.debug(f"Making LLM API call to model: {model_name} (Thinking: {enable_thinking}, Effort: {reasoning_effort})")
    params = prepare_params(
        messages=messages,
        model_name=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format=response_format,
        tools=tools,
        tool_choice=tool_choice,
        api_key=api_key,
        api_base=api_base,
        stream=stream,
        top_p=top_p,
        model_id=model_id,
        enable_thinking=enable_thinking,
        reasoning_effort=reasoning_effort,
        task_type=task_type
    )
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            logger.debug(f"Attempt {attempt + 1}/{MAX_RETRIES}")
            # logger.debug(f"API request parameters: {json.dumps(params, indent=2)}")
            
            response = await litellm.acompletion(**params)
            logger.debug(f"Successfully received API response from {model_name}")
            logger.debug(f"Response: {response}")
            return response
            
        except (litellm.exceptions.RateLimitError, OpenAIError, json.JSONDecodeError) as e:
            last_error = e
            await handle_error(e, attempt, MAX_RETRIES)
        except getattr(litellm.exceptions, 'BadRequestError', Exception) as e:
            # Handle missing LLM provider error by retrying with appropriate prefix
            if 'LLM Provider NOT provided' in str(e):
                # Check if it's an Ollama model
                if config.OLLAMA_PROVIDER and config.OLLAMA_PROVIDER.lower() == 'ollama':
                    logger.warning("LLM Provider missing, retrying with 'ollama/' prefix")
                    params['model'] = f"ollama/{params['model']}"
                else:
                    logger.warning("LLM Provider missing, retrying with 'openai/' prefix")
                    params['model'] = f"openai/{params['model']}"
                continue
            raise LLMError(f"API call failed: {str(e)}")
            
        except Exception as e:
            logger.error(f"Unexpected error during API call: {str(e)}", exc_info=True)
            raise LLMError(f"API call failed: {str(e)}")
    
    error_msg = f"Failed to make API call after {MAX_RETRIES} attempts"
    if last_error:
        error_msg += f". Last error: {str(last_error)}"
    logger.error(error_msg, exc_info=True)
    raise LLMRetryError(error_msg)

# Functions for Ollama model management
async def list_ollama_models() -> Dict[str, Any]:
    """
    List all available models on the Ollama server.
    
    Returns:
        Dict containing the list of available models and their details
    
    Raises:
        LLMError: If there's an error communicating with the Ollama server
    """
    import aiohttp
    
    if not config.OLLAMA_API_BASE:
        raise LLMError("Ollama API base URL not configured")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{config.OLLAMA_API_BASE}/api/tags") as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise LLMError(f"Failed to list Ollama models: {error_text}")
                
                result = await response.json()
                return result
    except Exception as e:
        logger.error(f"Error listing Ollama models: {str(e)}")
        raise LLMError(f"Failed to communicate with Ollama server: {str(e)}")

async def download_ollama_model(model_name: str) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Download a model to the Ollama server.
    
    Args:
        model_name: Name of the model to download (e.g., "llama3:8b")
    
    Yields:
        Dict containing progress updates during the download
    
    Raises:
        LLMError: If there's an error downloading the model
    """
    import aiohttp
    import json
    
    if not config.OLLAMA_API_BASE:
        raise LLMError("Ollama API base URL not configured")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{config.OLLAMA_API_BASE}/api/pull",
                json={"name": model_name},
                timeout=None  # No timeout for long downloads
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise LLMError(f"Failed to download model {model_name}: {error_text}")
                
                # Stream the response as it comes in
                async for line in response.content:
                    if line:
                        try:
                            progress = json.loads(line)
                            yield progress
                        except json.JSONDecodeError:
                            logger.warning(f"Received invalid JSON from Ollama: {line}")
                            continue
    except Exception as e:
        logger.error(f"Error downloading Ollama model {model_name}: {str(e)}")
        raise LLMError(f"Failed to download model {model_name}: {str(e)}")

async def select_ollama_model(model_name: str) -> bool:
    """
    Select an Ollama model as the default model to use.
    
    Args:
        model_name: Name of the model to set as default
    
    Returns:
        True if the model was successfully selected, False otherwise
    """
    # Check if the model exists on the Ollama server
    try:
        models = await list_ollama_models()
        available_models = [model["name"] for model in models.get("models", [])]
        
        if model_name not in available_models:
            logger.warning(f"Model {model_name} not found on Ollama server")
            return False
        
        # Update the configuration
        config.MODEL_TO_USE = model_name
        logger.info(f"Selected model: {model_name}")
        return True
    except Exception as e:
        logger.error(f"Error selecting Ollama model: {str(e)}")
        return False

# Initialize API keys on module import
setup_api_keys()

# Test code for OpenRouter integration
async def test_openrouter():
    """Test the OpenRouter integration with a simple query."""
    test_messages = [
        {"role": "user", "content": "Hello, can you give me a quick test response?"}
    ]
    
    try:
        # Test with standard OpenRouter model
        print("\n--- Testing standard OpenRouter model ---")
        response = await make_llm_api_call(
            model_name="openrouter/openai/gpt-4o-mini",
            messages=test_messages,
            temperature=0.7,
            max_tokens=100
        )
        print(f"Response: {response.choices[0].message.content}")
        
        # Test with deepseek model
        print("\n--- Testing deepseek model ---")
        response = await make_llm_api_call(
            model_name="openrouter/deepseek/deepseek-r1-distill-llama-70b",
            messages=test_messages,
            temperature=0.7,
            max_tokens=100
        )
        print(f"Response: {response.choices[0].message.content}")
        print(f"Model used: {response.model}")
        
        # Test with Mistral model
        print("\n--- Testing Mistral model ---")
        response = await make_llm_api_call(
            model_name="openrouter/mistralai/mixtral-8x7b-instruct",
            messages=test_messages,
            temperature=0.7,
            max_tokens=100
        )
        print(f"Response: {response.choices[0].message.content}")
        print(f"Model used: {response.model}")
        
        return True
    except Exception as e:
        print(f"Error testing OpenRouter: {str(e)}")
        return False

async def test_bedrock():
    """Test the AWS Bedrock integration with a simple query."""
    test_messages = [
        {"role": "user", "content": "Hello, can you give me a quick test response?"}
    ]
    
    try:    
        response = await make_llm_api_call(
            model_name="bedrock/anthropic.claude-3-7-sonnet-20250219-v1:0",
            model_id="arn:aws:bedrock:us-west-2:935064898258:inference-profile/us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            messages=test_messages,
            temperature=0.7,
            # Claude 3.7 has issues with max_tokens, so omit it
            # max_tokens=100
        )
        print(f"Response: {response.choices[0].message.content}")
        print(f"Model used: {response.model}")
        
        return True
    except Exception as e:
        print(f"Error testing Bedrock: {str(e)}")
        return False

if __name__ == "__main__":
    import asyncio
        
    test_success = asyncio.run(test_bedrock())
    
    if test_success:
        print("\n✅ integration test completed successfully!")
    else:
        print("\n❌ Bedrock integration test failed!")
