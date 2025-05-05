from agent.tools.web_search_tool import WebSearchTool
from agent.tools.sb_browser_tool import SandboxBrowserTool
from agentpress.tool import Tool, ToolResult, openapi_schema, xml_schema
from agentpress.thread_manager import ThreadManager
import json
import re
import logging
import asyncio

# Configure logging
logger = logging.getLogger(__name__)

class WeatherTool(Tool):
    """Tool for retrieving accurate weather information using browser navigation and web search."""

    def __init__(self, project_id: str = None, thread_id: str = None, thread_manager: ThreadManager = None, sandbox_id: str = None):
        super().__init__()
        # Initialize both tools
        self.web_search_tool = WebSearchTool()
        
        # Only initialize browser tool if the necessary params are provided
        self.browser_tool = None
        if project_id and thread_id and thread_manager:
            self.browser_tool = SandboxBrowserTool(project_id, thread_id, thread_manager, sandbox_id=sandbox_id)
            
        self.thread_id = thread_id
        self.project_id = project_id
        self.thread_manager = thread_manager
        self.sandbox_id = sandbox_id

    @openapi_schema({
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get accurate current weather information for a location using browser navigation to trusted weather sources and web search APIs. Returns temperature, conditions, and forecast details.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The location to get weather for (e.g., 'New York City', 'London, UK', 'Tokyo')"
                    },
                    "use_browser": {
                        "type": "boolean",
                        "description": "Whether to use browser navigation for more accurate results. Requires a browser session.",
                        "default": True
                    }
                },
                "required": ["location"]
            }
        }
    })
    @xml_schema(
        tag_name="get-weather",
        mappings=[
            {"param_name": "location", "node_type": "attribute", "path": "."},
            {"param_name": "use_browser", "node_type": "attribute", "path": "."}
        ],
        example='''
        <get-weather location="San Francisco" use_browser="true"></get-weather>
        
        <!-- Or more simply: -->
        <get-weather location="Paris"></get-weather>
        '''
    )
    async def get_weather(self, location: str, use_browser: bool = True) -> ToolResult:
        """
        Get accurate weather information for a location.
        
        This tool uses a combination of browser navigation to trusted weather sources
        and web search APIs to get the most accurate weather information.
        
        Args:
            location: The location to get weather for (e.g., 'New York City', 'London, UK')
            use_browser: Whether to use browser navigation for more accurate results
                        
        Returns:
            ToolResult with weather information including temperature, conditions, and forecast
        """
        logger.info(f"Getting weather for {location} (use_browser={use_browser})")
        
        weather_data = {
            "temperature": None,
            "conditions": None,
            "feels_like": None,
            "humidity": None,
            "wind": None,
            "forecast": None,
            "source": None,
            "location": location
        }
        
        # Track sources used for multi-source approach
        sources_tried = []
        
        # Try browser navigation first if available and enabled
        if use_browser and self.browser_tool:
            try:
                browser_weather = await self._get_weather_via_browser(location)
                if browser_weather and browser_weather.get("temperature"):
                    weather_data.update(browser_weather)
                    weather_data["source"] = "browser_navigation"
                    sources_tried.append("browser_navigation")
                    logger.info(f"Successfully obtained weather via browser: {browser_weather}")
                else:
                    logger.info("Browser navigation didn't return valid weather data")
            except Exception as e:
                logger.error(f"Error getting weather via browser: {str(e)}")
        
        # If browser failed or isn't available, try web search
        if not weather_data.get("temperature"):
            try:
                search_weather = await self._get_weather_via_search(location)
                if search_weather and search_weather.get("temperature"):
                    weather_data.update(search_weather)
                    if not weather_data.get("source"):
                        weather_data["source"] = "web_search"
                    else:
                        weather_data["source"] += "+web_search"
                    sources_tried.append("web_search")
                    logger.info(f"Successfully obtained weather via web search: {search_weather}")
                else:
                    logger.info("Web search didn't return valid weather data")
            except Exception as e:
                logger.error(f"Error getting weather via web search: {str(e)}")
        
        # Format a human-readable response
        if weather_data.get("temperature") or weather_data.get("conditions"):
            formatted_weather = self._format_weather_response(location, weather_data, sources_tried)
            
            return ToolResult(
                success=True,
                output=json.dumps({
                    "weather": formatted_weather,
                    "data": weather_data
                }, ensure_ascii=False)
            )
        else:
            return ToolResult(
                success=False,
                output=json.dumps({
                    "error": f"Could not retrieve weather information for {location} from any source",
                    "sources_tried": sources_tried
                }, ensure_ascii=False)
            )

    async def _get_weather_via_search(self, location: str) -> dict:
        """Use web search to get weather information"""
        query = f"weather in {location}"
        
        # Execute the web search
        result = await self.web_search_tool.web_search(query=query, num_results=5)
        
        if result.success and result.output:
            output_data = json.loads(result.output)
            
            if 'weather' in output_data:
                # Weather data is directly available
                return output_data.get('data', {})
            elif 'results' in output_data:
                # Need to extract weather data from search results
                return self.web_search_tool._extract_weather_data(output_data['results'])
        
        return {}

    async def _get_weather_via_browser(self, location: str) -> dict:
        """Use browser navigation to get weather from trusted sources"""
        if not self.browser_tool:
            return {}
            
        weather_data = {}
        
        # Define multiple weather websites to try
        weather_sites = [
            {
                "name": "Google Weather",
                "url": f"https://www.google.com/search?q=weather+in+{location}",
                "extractor": self._extract_google_weather
            },
            {
                "name": "AccuWeather",
                "url": f"https://www.accuweather.com/en/search-locations?query={location}",
                "extractor": self._extract_accuweather
            },
            {
                "name": "Weather.com",
                "url": f"https://weather.com/weather/today/l/{location.replace(' ', '+')}",
                "extractor": self._extract_weather_com
            },
            {
                "name": "Wunderground",
                "url": f"https://www.wunderground.com/weather/{location.replace(' ', '+')}",
                "extractor": self._extract_wunderground
            },
            {
                "name": "OpenWeatherMap",
                "url": f"https://openweathermap.org/find?q={location}",
                "extractor": self._extract_openweathermap
            },
            {
                "name": "WeatherBug",
                "url": f"https://www.weatherbug.com/weather-forecast/now/{location.replace(' ', '-')}",
                "extractor": self._extract_weatherbug
            }
        ]
        
        # Track which sites we've tried
        sites_tried = []
        
        try:
            # Log sandbox ID if available
            if self.sandbox_id:
                logger.info(f"Using sandbox ID: {self.sandbox_id} for browser navigation")
            
            # Try each weather site in sequence until we get valid data
            for site in weather_sites:
                site_name = site["name"]
                sites_tried.append(site_name)
                logger.info(f"Trying to retrieve weather from {site_name}")
                
                try:
                    # Navigate to the weather site
                    result = await self.browser_tool.browser_navigate_to(site["url"])
                    if not result.success:
                        logger.info(f"Failed to navigate to {site_name}")
                        continue
                    
                    logger.info(f"Successfully navigated to {site_name}")
                    
                    # Wait for the page to load
                    try:
                        await self.browser_tool.browser_wait(3)
                    except Exception as e:
                        logger.info(f"Wait action failed for {site_name}, but continuing: {str(e)}")
                    
                    # Get the page content directly from the navigation result
                    content = ""
                    
                    # First try to extract from the browser navigation result
                    if hasattr(result, 'data') and result.data:
                        if isinstance(result.data, dict):
                            # Try different possible content fields that might exist
                            for field in ['content', 'html', 'page_content', 'page_source', 'body']:
                                if field in result.data:
                                    content = result.data.get(field, '')
                                    if content:
                                        break
                            
                            # If we have title and url but no content, try to create a basic content
                            if not content and 'title' in result.data and 'url' in result.data:
                                content = f"Title: {result.data['title']}\nURL: {result.data['url']}"
                    
                    # If we still have no content, try browser state API (may not work in some environments)
                    if not content:
                        try:
                            browser_state = await self.browser_tool._execute_browser_action(
                                "get_updated_browser_state", 
                                {"action_name": f"check_weather_{site_name.lower().replace(' ', '_')}"}
                            )
                            
                            if browser_state.success:
                                content = self._extract_browser_content(browser_state)
                        except Exception as e:
                            logger.info(f"Browser state API call failed for {site_name}, but continuing: {str(e)}")
                    
                    # As a last resort, try to scrape the page using a direct curl command
                    if not content:
                        try:
                            # This is a special approach to get content when other methods fail
                            direct_curl_cmd = f"curl -s '{site['url']}'"
                            response = await self.browser_tool.sandbox.process.exec(direct_curl_cmd, timeout=10)
                            if response.exit_code == 0 and response.result:
                                content = response.result
                                logger.info(f"Used direct curl to extract content from {site_name}")
                        except Exception as e:
                            logger.info(f"Direct curl failed for {site_name}: {str(e)}")
                    
                    if content:
                        logger.info(f"Browser page content obtained from {site_name}, length: {len(content)}")
                        
                        # Use site-specific extractor
                        site_data = site["extractor"](content)
                        
                        # If we got valid temperature data, merge it and return
                        if site_data and site_data.get("temperature"):
                            weather_data.update(site_data)
                            weather_data["source"] = site_name
                            logger.info(f"Successfully extracted weather data from {site_name}: {site_data}")
                            return weather_data
                    else:
                        logger.info(f"No content extracted from {site_name}")
                
                except Exception as e:
                    logger.error(f"Error processing {site_name}: {str(e)}")
                
                # Try to go back, but don't fail if it doesn't work
                try:
                    await self.browser_tool.browser_go_back()
                except Exception as e:
                    logger.info(f"Browser go back failed for {site_name}, but continuing: {str(e)}")
                
            # If we get here, we tried all sites and failed
            logger.info(f"Tried all weather sites without success: {', '.join(sites_tried)}")
            
        except Exception as e:
            logger.error(f"Error navigating browser for weather: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
        return weather_data
    
    def _extract_browser_content(self, browser_state):
        """Extract content from browser state response"""
        content = ""
        
        # First try to get content from message field
        if hasattr(browser_state, 'message') and browser_state.message:
            content = browser_state.message
        
        # If that's empty, try to get it from the data.content field (for test mode)
        if not content and hasattr(browser_state, 'data') and browser_state.data:
            if isinstance(browser_state.data, dict) and 'content' in browser_state.data:
                content = browser_state.data.get('content', '')
            elif isinstance(browser_state.data, str):
                content = browser_state.data
        
        # As a fallback, try to use any data fields that might be useful
        if not content and hasattr(browser_state, 'data') and browser_state.data:
            if isinstance(browser_state.data, dict):
                # Create a text representation of the data
                content_parts = []
                for key, value in browser_state.data.items():
                    if isinstance(value, str):
                        content_parts.append(f"{key}: {value}")
                if content_parts:
                    content = "\n".join(content_parts)
                
        return content
    
    def _extract_google_weather(self, content):
        """Extract weather data from Google Weather page"""
        weather_data = {}
        
        if not content:
            return weather_data
            
        # Extract temperature (e.g., "54°")
        temp_match = re.search(r'(\d+)[°]', content)
        if temp_match:
            weather_data["temperature"] = f"{temp_match.group(1)}°"
            logger.info(f"Extracted temperature from Google: {weather_data['temperature']}")
        
        # Extract conditions
        for condition in ["sunny", "cloudy", "partly cloudy", "overcast", "rain", "raining",
                        "snow", "snowing", "thunderstorm", "fog", "foggy", "clear"]:
            if condition in content.lower():
                weather_data["conditions"] = condition
                logger.info(f"Extracted conditions from Google: {weather_data['conditions']}")
                break
        
        # Extract humidity
        humidity_match = re.search(r'Humidity:\s*(\d+)%', content)
        if humidity_match:
            weather_data["humidity"] = f"{humidity_match.group(1)}%"
            logger.info(f"Extracted humidity from Google: {weather_data['humidity']}")
        
        # Extract wind
        wind_match = re.search(r'Wind:\s*(\d+\s*mph)', content)
        if wind_match:
            weather_data["wind"] = wind_match.group(1)
            logger.info(f"Extracted wind from Google: {weather_data['wind']}")
            
        # Extract feels like
        feels_match = re.search(r'Feels like\s*(\d+)[°]', content)
        if feels_match:
            weather_data["feels_like"] = f"{feels_match.group(1)}°"
            logger.info(f"Extracted feels like from Google: {weather_data['feels_like']}")
            
        return weather_data
    
    def _extract_accuweather(self, content):
        """Extract weather data from AccuWeather page"""
        weather_data = {}
        
        if not content:
            return weather_data
            
        # Extract temperature
        temp_match = re.search(r'(\d+)°[FC]?', content)
        if temp_match:
            weather_data["temperature"] = f"{temp_match.group(1)}°"
            logger.info(f"Extracted temperature from AccuWeather: {weather_data['temperature']}")
        
        # Extract conditions
        condition_patterns = [
            r'Currently\s*:\s*([A-Za-z\s]+)',
            r'Current\s*Weather\s*:\s*([A-Za-z\s]+)'
        ]
        for pattern in condition_patterns:
            match = re.search(pattern, content)
            if match:
                weather_data["conditions"] = match.group(1).strip().lower()
                logger.info(f"Extracted conditions from AccuWeather: {weather_data['conditions']}")
                break
                
        # If no specific pattern matched, try common weather conditions
        if not weather_data.get("conditions"):
            for condition in ["sunny", "cloudy", "partly cloudy", "overcast", "rain", "raining",
                            "snow", "snowing", "thunderstorm", "fog", "foggy", "clear"]:
                if condition in content.lower():
                    weather_data["conditions"] = condition
                    logger.info(f"Extracted conditions from AccuWeather using keywords: {weather_data['conditions']}")
                    break
        
        # Extract humidity
        humidity_match = re.search(r'Humidity\s*:?\s*(\d+)%', content, re.IGNORECASE)
        if humidity_match:
            weather_data["humidity"] = f"{humidity_match.group(1)}%"
            logger.info(f"Extracted humidity from AccuWeather: {weather_data['humidity']}")
        
        # Extract wind
        wind_matches = re.search(r'Wind\s*:?\s*([\d\.]+\s*(?:mph|km/h|m/s))', content, re.IGNORECASE)
        if wind_matches:
            weather_data["wind"] = wind_matches.group(1)
            logger.info(f"Extracted wind from AccuWeather: {weather_data['wind']}")
            
        # Extract feels like
        feels_match = re.search(r'(?:Feels Like|RealFeel)[^0-9]*(\d+)[°]', content, re.IGNORECASE)
        if feels_match:
            weather_data["feels_like"] = f"{feels_match.group(1)}°"
            logger.info(f"Extracted feels like from AccuWeather: {weather_data['feels_like']}")
            
        return weather_data
    
    def _extract_weather_com(self, content):
        """Extract weather data from Weather.com page"""
        weather_data = {}
        
        if not content:
            return weather_data
            
        # Extract temperature
        temp_match = re.search(r'(\d+)°[FC]?', content)
        if temp_match:
            weather_data["temperature"] = f"{temp_match.group(1)}°"
            logger.info(f"Extracted temperature from Weather.com: {weather_data['temperature']}")
        
        # Extract conditions
        condition_patterns = [
            r'class="CurrentConditions--phraseValue--[^"]+">([^<]+)',
            r'Currently:\s*([A-Za-z\s]+)',
            r'Current Conditions\s*:\s*([A-Za-z\s]+)'
        ]
        
        for pattern in condition_patterns:
            match = re.search(pattern, content)
            if match:
                weather_data["conditions"] = match.group(1).strip().lower()
                logger.info(f"Extracted conditions from Weather.com: {weather_data['conditions']}")
                break
                
        # If no specific pattern matched, try common weather conditions
        if not weather_data.get("conditions"):
            for condition in ["sunny", "cloudy", "partly cloudy", "overcast", "rain", "raining",
                             "snow", "snowing", "thunderstorm", "fog", "foggy", "clear"]:
                if condition in content.lower():
                    weather_data["conditions"] = condition
                    logger.info(f"Extracted conditions from Weather.com using keywords: {weather_data['conditions']}")
                    break
        
        # Extract humidity
        humidity_match = re.search(r'Humidity\s*:?\s*(\d+)%', content, re.IGNORECASE)
        if humidity_match:
            weather_data["humidity"] = f"{humidity_match.group(1)}%"
            logger.info(f"Extracted humidity from Weather.com: {weather_data['humidity']}")
        
        # Extract wind
        wind_matches = re.search(r'Wind\s*:?\s*([\d\.]+\s*(?:mph|km/h|m/s))', content, re.IGNORECASE)
        if wind_matches:
            weather_data["wind"] = wind_matches.group(1)
            logger.info(f"Extracted wind from Weather.com: {weather_data['wind']}")
            
        # Extract feels like
        feels_match = re.search(r'Feels Like[^0-9]*(\d+)[°]', content, re.IGNORECASE)
        if feels_match:
            weather_data["feels_like"] = f"{feels_match.group(1)}°"
            logger.info(f"Extracted feels like from Weather.com: {weather_data['feels_like']}")
            
        return weather_data
    
    def _extract_wunderground(self, content):
        """Extract weather data from Weather Underground page"""
        weather_data = {}
        
        if not content:
            return weather_data
            
        # Extract temperature
        temp_match = re.search(r'(\d+)°[FC]?', content)
        if temp_match:
            weather_data["temperature"] = f"{temp_match.group(1)}°"
            logger.info(f"Extracted temperature from Wunderground: {weather_data['temperature']}")
        
        # Extract conditions
        condition_patterns = [
            r'Condition[^:]*:\s*([A-Za-z\s]+)',
            r'As of [^:]+:\s*([A-Za-z\s]+)',
            r'Currently:\s*([A-Za-z\s]+)'
        ]
        
        for pattern in condition_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                weather_data["conditions"] = match.group(1).strip().lower()
                logger.info(f"Extracted conditions from Wunderground: {weather_data['conditions']}")
                break
                
        # If no specific pattern matched, try common weather conditions
        if not weather_data.get("conditions"):
            for condition in ["sunny", "cloudy", "partly cloudy", "overcast", "rain", "raining",
                             "snow", "snowing", "thunderstorm", "fog", "foggy", "clear"]:
                if condition in content.lower():
                    weather_data["conditions"] = condition
                    logger.info(f"Extracted conditions from Wunderground using keywords: {weather_data['conditions']}")
                    break
        
        # Extract humidity
        humidity_match = re.search(r'Humidity\s*:?\s*(\d+)%', content, re.IGNORECASE)
        if humidity_match:
            weather_data["humidity"] = f"{humidity_match.group(1)}%"
            logger.info(f"Extracted humidity from Wunderground: {weather_data['humidity']}")
        
        # Extract wind
        wind_match = re.search(r'Wind\s*:?\s*([\d\.]+\s*(?:mph|km/h|m/s))', content, re.IGNORECASE)
        if wind_match:
            weather_data["wind"] = wind_match.group(1)
            logger.info(f"Extracted wind from Wunderground: {weather_data['wind']}")
            
        # Extract feels like
        feels_match = re.search(r'Feels Like[^0-9]*(\d+)[°]', content, re.IGNORECASE)
        if feels_match:
            weather_data["feels_like"] = f"{feels_match.group(1)}°"
            logger.info(f"Extracted feels like from Wunderground: {weather_data['feels_like']}")
            
        return weather_data

    def _extract_openweathermap(self, content):
        """Extract weather data from OpenWeatherMap page"""
        weather_data = {}
        
        if not content:
            return weather_data
            
        # Extract temperature
        temp_match = re.search(r'(\d+\.?\d*)\s*°[FC]', content)
        if temp_match:
            weather_data["temperature"] = f"{int(float(temp_match.group(1)))}°"
            logger.info(f"Extracted temperature from OpenWeatherMap: {weather_data['temperature']}")
        
        # Extract conditions
        condition_patterns = [
            r'class="weather-widget__main"[^>]*>([^<]+)',
            r'class="heading"[^>]*>([^<]+)<',
            r'class="condition"[^>]*>([^<]+)<'
        ]
        
        for pattern in condition_patterns:
            match = re.search(pattern, content)
            if match:
                weather_data["conditions"] = match.group(1).strip().lower()
                logger.info(f"Extracted conditions from OpenWeatherMap: {weather_data['conditions']}")
                break
                
        # If no specific pattern matched, try common weather conditions
        if not weather_data.get("conditions"):
            for condition in ["sunny", "cloudy", "partly cloudy", "overcast", "rain", "raining",
                            "snow", "snowing", "thunderstorm", "fog", "foggy", "clear"]:
                if condition in content.lower():
                    weather_data["conditions"] = condition
                    logger.info(f"Extracted conditions from OpenWeatherMap using keywords: {weather_data['conditions']}")
                    break
        
        # Extract humidity
        humidity_match = re.search(r'Humidity:\s*(\d+)%', content, re.IGNORECASE)
        if humidity_match:
            weather_data["humidity"] = f"{humidity_match.group(1)}%"
            logger.info(f"Extracted humidity from OpenWeatherMap: {weather_data['humidity']}")
        
        # Extract wind
        wind_match = re.search(r'Wind:\s*([\d\.]+\s*(?:mph|km/h|m/s))', content, re.IGNORECASE)
        if wind_match:
            weather_data["wind"] = wind_match.group(1)
            logger.info(f"Extracted wind from OpenWeatherMap: {weather_data['wind']}")
            
        # Extract feels like
        feels_match = re.search(r'Feels like[^0-9]*(\d+)[°]', content, re.IGNORECASE)
        if feels_match:
            weather_data["feels_like"] = f"{feels_match.group(1)}°"
            logger.info(f"Extracted feels like from OpenWeatherMap: {weather_data['feels_like']}")
            
        return weather_data
    
    def _extract_weatherbug(self, content):
        """Extract weather data from WeatherBug page"""
        weather_data = {}
        
        if not content:
            return weather_data
            
        # Extract temperature
        temp_match = re.search(r'class="[^"]*current-temp[^"]*"[^>]*>(\d+)[°]', content)
        if not temp_match:
            temp_match = re.search(r'(\d+)[°][FC]?', content)
            
        if temp_match:
            weather_data["temperature"] = f"{temp_match.group(1)}°"
            logger.info(f"Extracted temperature from WeatherBug: {weather_data['temperature']}")
        
        # Extract conditions
        condition_patterns = [
            r'class="[^"]*current-conditions[^"]*"[^>]*>([^<]+)',
            r'weather-condition[^>]*>([^<]+)',
            r'weather-phrase[^>]*>([^<]+)'
        ]
        
        for pattern in condition_patterns:
            match = re.search(pattern, content)
            if match:
                weather_data["conditions"] = match.group(1).strip().lower()
                logger.info(f"Extracted conditions from WeatherBug: {weather_data['conditions']}")
                break
                
        # If no specific pattern matched, try common weather conditions
        if not weather_data.get("conditions"):
            for condition in ["sunny", "cloudy", "partly cloudy", "overcast", "rain", "raining",
                             "snow", "snowing", "thunderstorm", "fog", "foggy", "clear"]:
                if condition in content.lower():
                    weather_data["conditions"] = condition
                    logger.info(f"Extracted conditions from WeatherBug using keywords: {weather_data['conditions']}")
                    break
        
        # Extract humidity
        humidity_match = re.search(r'Humidity[^:]*:\s*(\d+)%', content, re.IGNORECASE)
        if humidity_match:
            weather_data["humidity"] = f"{humidity_match.group(1)}%"
            logger.info(f"Extracted humidity from WeatherBug: {weather_data['humidity']}")
        
        # Extract wind
        wind_match = re.search(r'Wind[^:]*:\s*([\d\.]+\s*(?:mph|km/h|m/s))', content, re.IGNORECASE)
        if wind_match:
            weather_data["wind"] = wind_match.group(1)
            logger.info(f"Extracted wind from WeatherBug: {weather_data['wind']}")
            
        # Extract feels like
        feels_match = re.search(r'Feels Like[^0-9]*(\d+)[°]', content, re.IGNORECASE)
        if feels_match:
            weather_data["feels_like"] = f"{feels_match.group(1)}°"
            logger.info(f"Extracted feels like from WeatherBug: {weather_data['feels_like']}")
            
        return weather_data

    def _format_weather_response(self, location: str, weather_data: dict, sources: list) -> str:
        """Format weather data into a human-readable response."""
        weather_info = [f"Current weather in {location}:"]
        
        # Handle temperature and conditions
        if weather_data.get("temperature") and weather_data.get("conditions"):
            weather_info.append(f"Temperature: {weather_data['temperature']}, Conditions: {weather_data['conditions']}")
        elif weather_data.get("temperature"):
            weather_info.append(f"Temperature: {weather_data['temperature']}")
        elif weather_data.get("conditions"):
            weather_info.append(f"Conditions: {weather_data['conditions']}")
        else:
            weather_info.append("Specific temperature and conditions data isn't available.")
            
        # Add additional details if available
        if weather_data.get("feels_like"):
            weather_info.append(f"Feels like: {weather_data['feels_like']}")
        if weather_data.get("humidity"):
            weather_info.append(f"Humidity: {weather_data['humidity']}")
        if weather_data.get("wind"):
            weather_info.append(f"Wind: {weather_data['wind']}")
            
        # Add forecast data if available
        if weather_data.get("forecast"):
            forecast_text = weather_data["forecast"]
            # Format if needed
            if len(forecast_text) > 100:
                forecast_text = forecast_text[:100] + "..."
            weather_info.append(f"Forecast: {forecast_text}")
        
        # Add source information
        weather_info.append(f"\nData sourced from: {', '.join(sources)}")
        
        return "\n".join(weather_info) 