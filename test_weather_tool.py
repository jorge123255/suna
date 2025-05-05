#!/usr/bin/env python3
"""
Test script for WeatherTool that combines browser navigation and web search
"""

import asyncio
import os
import sys
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("weather_tool_test")

# Import the tools
from agent.tools.weather_tool import WeatherTool
from agentpress.thread_manager import ThreadManager
from sandbox.sandbox import get_or_start_sandbox

def validate_temperature(temp_string):
    """Validate that a temperature value is reasonable"""
    if not temp_string:
        return False
        
    # Extract just the number from formats like "75°"
    temp_match = temp_string.replace('°', '')
    try:
        temp_value = int(temp_match)
        # Valid temperatures on Earth generally range from -60° to 130°
        return -60 <= temp_value <= 130
    except (ValueError, TypeError):
        return False

async def test_weather_tool(location="New York City", use_browser=True):
    """Test the WeatherTool with a location"""
    try:
        logger.info(f"=== Testing WeatherTool for location: {location} (use_browser={use_browser}) ===")
        
        # Create thread manager with direct sandbox ID
        thread_manager = ThreadManager()
        
        # Setup a minimal mock for the DB connection
        class MockDB:
            async def get_client(self):
                return None
            client = property(get_client)
            
        thread_manager.db = MockDB()
        
        # Use the provided sandbox ID
        sandbox_id = "69663ff8-a836-40a3-882b-1a6ad0c68678"
        
        # Generate test IDs for the browser tool
        project_id = "test-project"
        thread_id = "test-thread"
        
        # Create the weather tool instance
        logger.info("Creating WeatherTool instance...")
        weather_tool = WeatherTool(project_id, thread_id, thread_manager, sandbox_id=sandbox_id)
        
        # Execute the weather query
        logger.info(f"Getting weather for {location}...")
        result = await weather_tool.get_weather(location=location, use_browser=use_browser)
        
        # Print the result
        logger.info(f"Weather query completed with success: {result.success}")
        
        if result.output:
            logger.info(f"Output type: {type(result.output)}")
            output_data = json.loads(result.output)
            
            logger.info(f"Output keys: {list(output_data.keys())}")
            
            if 'weather' in output_data:
                logger.info("Weather data extracted successfully!")
                logger.info(f"Weather: {output_data['weather']}")
                logger.info(f"Weather data: {output_data['data']}")
                
                # Validate the temperature
                temp = output_data['data'].get('temperature')
                if temp:
                    is_valid_temp = validate_temperature(temp)
                    logger.info(f"Temperature '{temp}' is valid: {is_valid_temp}")
                    if not is_valid_temp:
                        logger.warning(f"Invalid temperature detected: {temp}")
                
                return True, output_data
            else:
                logger.info("No weather data in output")
                if 'error' in output_data:
                    logger.error(f"Error: {output_data['error']}")
                return False, output_data
        else:
            logger.info("No output in result")
            return False, None
    
    except Exception as e:
        logger.error(f"Error during weather tool test: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False, None

async def main():
    """Main function to run the tests"""
    logger.info("Starting WeatherTool tests with both web search and browser navigation")
    
    # Test with various locations
    test_locations = [
        "New York City",
        "San Francisco",
        "London, UK"
    ]
    
    # Test with browser first
    logger.info("\n=== TESTING WITH BROWSER NAVIGATION ===")
    for location in test_locations:
        success, data = await test_weather_tool(location, use_browser=True)
        logger.info(f"Browser test for '{location}': {'Success' if success else 'Failed'}")
        logger.info("-" * 50)
    
    # Test with web search only
    logger.info("\n=== TESTING WITH WEB SEARCH ONLY ===")
    for location in test_locations:
        success, data = await test_weather_tool(location, use_browser=False)
        logger.info(f"Web search test for '{location}': {'Success' if success else 'Failed'}")
        logger.info("-" * 50)
    
    logger.info("Tests completed")

if __name__ == "__main__":
    asyncio.run(main()) 