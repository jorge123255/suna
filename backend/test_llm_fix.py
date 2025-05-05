#!/usr/bin/env python
"""
Test script to verify the LLM provider prefix fix.
This script tests both the automatic provider prefixing and the BadRequestError handling.
"""

import asyncio
import sys
import os
from services.llm import make_llm_api_call
from utils.logger import logger

async def test_model_provider_fix():
    """Test the automatic model provider prefixing."""
    logger.info("Testing model provider prefix fix...")
    
    # Test case 1: Model without provider prefix
    try:
        logger.info("Test 1: Calling model without provider prefix")
        response = await make_llm_api_call(
            messages=[{"role": "user", "content": "Hello, this is a test of the provider prefix fix."}],
            model_name="gpt-3.5-turbo",  # No provider prefix
            temperature=0.7,
            max_tokens=50
        )
        logger.info(f"Success! Response received: {response.choices[0].message.content}")
        return True
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        return False

async def main():
    """Run all tests."""
    success = await test_model_provider_fix()
    
    if success:
        logger.info("All tests passed! The LLM provider prefix fix is working correctly.")
        return 0
    else:
        logger.error("Tests failed. The LLM provider prefix fix is not working correctly.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
