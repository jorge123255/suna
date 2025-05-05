from tavily import AsyncTavilyClient
import httpx
from typing import List, Optional
from datetime import datetime
import os
from dotenv import load_dotenv
from agentpress.tool import Tool, ToolResult, openapi_schema, xml_schema
from utils.config import config
import json
import re
import logging

# Configure logging
logger = logging.getLogger(__name__)

# TODO: add subpages, etc... in filters as sometimes its necessary 

class WebSearchTool(Tool):
    """Tool for performing web searches using Tavily API and web scraping using Firecrawl."""

    def __init__(self, api_key: str = None):
        super().__init__()
        # Load environment variables
        load_dotenv()
        # Use the provided API key or get it from environment variables
        self.tavily_api_key = api_key or config.TAVILY_API_KEY
        self.firecrawl_api_key = config.FIRECRAWL_API_KEY
        
        if not self.tavily_api_key:
            raise ValueError("TAVILY_API_KEY not found in configuration")
        if not self.firecrawl_api_key:
            raise ValueError("FIRECRAWL_API_KEY not found in configuration")

        # Tavily asynchronous search client
        self.tavily_client = AsyncTavilyClient(api_key=self.tavily_api_key)

    @openapi_schema({
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for up-to-date information on a specific topic using the Tavily API. This tool allows you to gather real-time information from the internet to answer user queries, research topics, validate facts, and find recent developments. Results include titles, URLs, summaries, and publication dates. Use this tool for discovering relevant web pages before potentially crawling them for complete content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to find relevant web pages. Be specific and include key terms to improve search accuracy. For best results, use natural language questions or keyword combinations that precisely describe what you're looking for."
                    },
                    # "summary": {
                    #     "type": "boolean",
                    #     "description": "Whether to include a summary of each search result. Summaries provide key context about each page without requiring full content extraction. Set to true to get concise descriptions of each result.",
                    #     "default": True
                    # },
                    "num_results": {
                        "type": "integer",
                        "description": "The number of search results to return. Increase for more comprehensive research or decrease for focused, high-relevance results.",
                        "default": 20
                    }
                },
                "required": ["query"]
            }
        }
    })
    @xml_schema(
        tag_name="web-search",
        mappings=[
            {"param_name": "query", "node_type": "attribute", "path": "."},
            # {"param_name": "summary", "node_type": "attribute", "path": "."},
            {"param_name": "num_results", "node_type": "attribute", "path": "."}
        ],
        example='''
        <!-- 
        The web-search tool allows you to search the internet for real-time information.
        Use this tool when you need to find current information, research topics, or verify facts.
        
        The tool returns information including:
        - Titles of relevant web pages
        - URLs for accessing the pages
        - Published dates (when available)
        -->
        
        <!-- Simple search example -->
        <web-search 
            query="current weather in New York City" 
            num_results="20">
        </web-search>
        
        <!-- Another search example -->
        <web-search 
            query="healthy breakfast recipes" 
            num_results="20">
        </web-search>
        '''
    )
    async def web_search(self, query: str, num_results: int = 20) -> ToolResult:
        """
        Search the web using the Tavily API to find relevant and up-to-date information.
        
        Args:
            query: The search query
            num_results: The number of results to return
            
        Returns:
            ToolResult containing the search results with enhanced information
        """
        try:
            # Log the query to aid in debugging
            logger.info(f"WebSearchTool: Processing query '{query}'")
            
            # Ensure we have a valid query
            if not query or not isinstance(query, str):
                return self.fail_response("A valid search query is required.")
            
            # Normalize num_results
            if num_results is None:
                num_results = 20
            elif isinstance(num_results, int):
                num_results = max(1, min(num_results, 50))
            elif isinstance(num_results, str):
                try:
                    num_results = max(1, min(int(num_results), 50))
                except ValueError:
                    num_results = 20
            else:
                num_results = 20

            # Execute the search with Tavily
            search_response = await self.tavily_client.search(
                query=query,
                max_results=num_results,
                include_answer=True,  # Get the answer for better results
                include_images=False,
                include_raw_content=True,  # Ensure we get raw content for processing
            )

            # Normalize the response format
            raw_results = (
                search_response.get("results")
                if isinstance(search_response, dict)
                else search_response
            )

            # Check if we have any results
            if not raw_results:
                logger.warning("No search results found")
                return self.success_response({
                    "results": [],
                    "message": "No search results found. Consider refining your query or using browser navigation.",
                    "status": "no_results"
                })
                
            # Process the results to extract the most relevant information
            enhanced_results = self._process_search_results(raw_results, query)
            
            # Add metadata to help the agent understand the results
            response = {
                "results": enhanced_results,
                "original_query": query,
                "result_count": len(enhanced_results),
                "status": "success",
                "message": f"Found {len(enhanced_results)} results for '{query}'"
            }
            
            # For weather queries, try to extract actual weather information
            if self._is_weather_query(query):
                logger.info(f"WebSearchTool: Processing weather query: {query}")
                try:
                    # Extract location from the query
                    location = self._extract_location(query)
                    logger.info(f"WebSearchTool: Extracted location: {location}")
                    
                    # Extract weather details from search results
                    weather_data = self._extract_weather_data(enhanced_results)
                    logger.info(f"WebSearchTool: Extracted weather data: {weather_data}")
                    
                    if weather_data.get("temperature") or weather_data.get("conditions"):
                        # Format weather information into a readable response
                        weather_info = self._format_weather_response(location, weather_data)
                        response["weather_summary"] = weather_info
                except Exception as weather_error:
                    # Log but don't fail - fall back to regular search results
                    logger.error(f"WebSearchTool: Error processing weather data: {str(weather_error)}")
            
            return self.success_response(response)
            
        except Exception as e:
            logger.error(f"Error searching web: {e}")
            return self.fail_response(f"Error searching web: {e}")
            
    def _process_search_results(self, results, query):
        """Process search results to extract the most relevant information.
        
        Args:
            results: The raw search results from Tavily
            query: The original search query
            
        Returns:
            Enhanced results with extracted information
        """
        formatted_results = []
        for result in results:
            formatted_result = {
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "snippet": result.get("content") or result.get("description") or "",
            }
            
            formatted_results.append(formatted_result)
        
        return formatted_results
    
    def _is_weather_query(self, query: str) -> bool:
        """Determine if a query is asking about weather."""
        weather_patterns = [
            r'weather\s+in\s+(\w+)',
            r'(\w+)\s+weather',
            r'temperature\s+in\s+(\w+)',
            r'how\s+is\s+the\s+weather\s+in\s+(\w+)',
            r'forecast\s+for\s+(\w+)',
            r'weather\s+for\s+(\w+)',
            r'weather\s+like\s+in\s+(\w+)'
        ]
        
        for pattern in weather_patterns:
            if re.search(pattern, query.lower()):
                return True
                
        return False
    
    def _extract_location(self, query: str) -> str:
        """Extract location from a weather query."""
        patterns = [
            r'weather\s+in\s+([A-Za-z\s,]+)(?:\W|$)',
            r'([A-Za-z\s,]+)\s+weather',
            r'temperature\s+in\s+([A-Za-z\s,]+)(?:\W|$)',
            r'how\s+is\s+the\s+weather\s+in\s+([A-Za-z\s,]+)(?:\W|$)',
            r'forecast\s+for\s+([A-Za-z\s,]+)(?:\W|$)',
            r'weather\s+for\s+([A-Za-z\s,]+)(?:\W|$)',
            r'weather\s+like\s+in\s+([A-Za-z\s,]+)(?:\W|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1).strip()
                
        return "the requested location"
    
    def _extract_weather_data(self, search_results: list) -> dict:
        """Extract weather data from search results."""
        weather_data = {
            "temperature": None,
            "conditions": None,
            "feels_like": None,
            "humidity": None,
            "wind": None,
            "forecast": None
        }
        
        condition_keywords = [
            "sunny", "cloudy", "partly cloudy", "overcast", "rain", "raining",
            "snow", "snowing", "thunderstorm", "fog", "foggy", "haze", "hazy",
            "clear", "fair", "windy", "stormy", "showers", "drizzle"
        ]
        
        # Process snippets to extract weather information
        for result in search_results:
            snippet = result.get("snippet", "").lower()
            
            # Temperature extraction (prioritize exact matches first)
            if not weather_data["temperature"]:
                temp_matches = re.findall(r'(\d+)[°]?[cf]', snippet)
                if temp_matches:
                    weather_data["temperature"] = f"{temp_matches[0]}°"
                
            # Conditions extraction
            if not weather_data["conditions"]:
                for keyword in condition_keywords:
                    if keyword in snippet:
                        weather_data["conditions"] = keyword
                        break
                    
            # Other weather data extraction
            if not weather_data["feels_like"]:
                feels_like_matches = re.findall(r'feels like (\d+)[°]?[cf]', snippet)
                if feels_like_matches:
                    weather_data["feels_like"] = f"{feels_like_matches[0]}°"
                    
            if not weather_data["humidity"]:
                humidity_matches = re.findall(r'humidity[:\s]+(\d+)%', snippet)
                if humidity_matches:
                    weather_data["humidity"] = f"{humidity_matches[0]}%"
                    
            if not weather_data["wind"]:
                wind_matches = re.findall(r'wind[:\s]+(\d+\s*mph)', snippet)
                if wind_matches:
                    weather_data["wind"] = wind_matches[0]
                    
            if not weather_data["forecast"] and ("forecast" in snippet or "expected" in snippet or "will be" in snippet):
                weather_data["forecast"] = snippet
        
        return weather_data
    
    def _format_weather_response(self, location: str, weather_data: dict) -> str:
        """Format weather data into a human-readable response."""
        weather_info = [f"Current weather in {location}:"]
        
        if weather_data["temperature"] and weather_data["conditions"]:
            weather_info.append(f"Temperature: {weather_data['temperature']}, Conditions: {weather_data['conditions']}")
        elif weather_data["temperature"]:
            weather_info.append(f"Temperature: {weather_data['temperature']}")
        elif weather_data["conditions"]:
            weather_info.append(f"Conditions: {weather_data['conditions']}")
            
        if weather_data["feels_like"]:
            weather_info.append(f"Feels like: {weather_data['feels_like']}")
        if weather_data["humidity"]:
            weather_info.append(f"Humidity: {weather_data['humidity']}")
        if weather_data["wind"]:
            weather_info.append(f"Wind: {weather_data['wind']}")
        if weather_data["forecast"]:
            weather_info.append(f"Forecast: {weather_data['forecast'][:100]}...")
            
        return "\n".join(weather_info)

    @openapi_schema({
        "type": "function",
        "function": {
            "name": "scrape_webpage",
            "description": "Retrieve the complete text content of a specific webpage using Firecrawl. This tool extracts the full text content from any accessible web page and returns it for analysis, processing, or reference. The extracted text includes the main content of the page without HTML markup. Note that some pages may have limitations on access due to paywalls, access restrictions, or dynamic content loading.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The complete URL of the webpage to scrape. This should be a valid, accessible web address including the protocol (http:// or https://). The tool will attempt to extract all text content from this URL."
                    }
                },
                "required": ["url"]
            }
        }
    })
    @xml_schema(
        tag_name="scrape-webpage",
        mappings=[
            {"param_name": "url", "node_type": "attribute", "path": "."}
        ],
        example='''
        <!-- 
        The scrape-webpage tool extracts the complete text content from web pages using Firecrawl.
        IMPORTANT WORKFLOW RULES:
        1. ALWAYS use web-search first to find relevant URLs
        2. Then use scrape-webpage on URLs from web-search results
        3. Only if scrape-webpage fails or if the page requires interaction:
           - Use direct browser tools (browser_navigate_to, browser_click_element, etc.)
           - This is needed for dynamic content, JavaScript-heavy sites, or pages requiring interaction
        
        Firecrawl Features:
        - Converts web pages into clean markdown
        - Handles dynamic content and JavaScript-rendered sites
        - Manages proxies, caching, and rate limits
        - Supports PDFs and images
        - Outputs clean markdown
        -->
        
        <!-- Example workflow: -->
        <!-- 1. First search for relevant content -->
        <web-search 
            query="latest AI research papers" 
            # summary="true"
            num_results="5">
        </web-search>
        
        <!-- 2. Then scrape specific URLs from search results -->
        <scrape-webpage 
            url="https://example.com/research/ai-paper-2024">
        </scrape-webpage>
        
        <!-- 3. Only if scrape fails or interaction needed, use browser tools -->
        <!-- Example of when to use browser tools:
             - Dynamic content loading
             - JavaScript-heavy sites
             - Pages requiring login
             - Interactive elements
             - Infinite scroll pages
        -->
        '''
    )
    async def scrape_webpage(
        self,
        url: str
    ) -> ToolResult:
        """
        Retrieve the complete text content of a webpage using Firecrawl.
        
        This function scrapes the specified URL and extracts the full text content from the page.
        The extracted text is returned in the response, making it available for further analysis,
        processing, or reference.
        
        The returned data includes:
        - Title: The title of the webpage
        - URL: The URL of the scraped page
        - Published Date: When the content was published (if available)
        - Text: The complete text content of the webpage in markdown format
        
        Note that some pages may have limitations on access due to paywalls, 
        access restrictions, or dynamic content loading.
        
        Parameters:
        - url: The URL of the webpage to scrape
        """
        try:
            # Parse the URL parameter exactly as it would appear in XML
            if not url:
                return self.fail_response("A valid URL is required.")
                
            # Handle url parameter (as it would appear in XML)
            if isinstance(url, str):
                # Add protocol if missing
                if not (url.startswith('http://') or url.startswith('https://')):
                    url = 'https://' + url
            else:
                return self.fail_response("URL must be a string.")
                
            # ---------- Firecrawl scrape endpoint ----------
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.firecrawl_api_key}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "url": url,
                    "formats": ["markdown"]
                }
                response = await client.post(
                    "https://api.firecrawl.dev/v1/scrape",
                    json=payload,
                    headers=headers,
                    timeout=60,
                )
                response.raise_for_status()
                data = response.json()

            # Format the response
            formatted_result = {
                "Title": data.get("data", {}).get("metadata", {}).get("title", ""),
                "URL": url,
                "Text": data.get("data", {}).get("markdown", "")
            }
            
            # Add metadata if available
            if "metadata" in data.get("data", {}):
                formatted_result["Metadata"] = data["data"]["metadata"]
            
            return self.success_response([formatted_result])
        
        except Exception as e:
            error_message = str(e)
            # Truncate very long error messages
            simplified_message = f"Error scraping webpage: {error_message[:200]}"
            if len(error_message) > 200:
                simplified_message += "..."
            return self.fail_response(simplified_message)


if __name__ == "__main__":
    import asyncio
    
    async def test_web_search():
        """Test function for the web search tool"""
        search_tool = WebSearchTool()
        result = await search_tool.web_search(
            query="weather in Chicago",
            num_results=20
        )
        print(f"Weather query test result: {result}")
        print(f"Output: {result.output if hasattr(result, 'output') else 'No output'}")
        print(f"Message: {result.message if hasattr(result, 'message') else 'No message'}")
        
        # Test a non-weather query
        result2 = await search_tool.web_search(
            query="latest AI research",
            num_results=5
        )
        print(f"Regular query test result: {result2}")
    
    async def test_scrape_webpage():
        """Test function for the webpage scrape tool"""
        search_tool = WebSearchTool()
        result = await search_tool.scrape_webpage(
            url="https://www.wired.com/story/anthropic-benevolent-artificial-intelligence/"
        )
        print(result)
    
    async def run_tests():
        """Run all test functions"""
        print("Testing weather query...")
        await test_web_search()
        print("\nTesting webpage scraping...")
        await test_scrape_webpage()
        
    asyncio.run(run_tests())