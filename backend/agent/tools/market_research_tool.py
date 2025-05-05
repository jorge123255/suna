"""
Market Research Tool

This module provides a dedicated tool for conducting comprehensive market research
and generating structured reports with company profiles and market analysis.
"""

import json
import os
from typing import Dict, Any, List, Optional
from agentpress.tool import Tool, ToolResult, openapi_schema, xml_schema
from agentpress.thread_manager import ThreadManager
from utils.logger import logger
import traceback
from sandbox.sandbox import SandboxToolsBase

class MarketResearchTool(Tool):
    """Tool for conducting comprehensive market research and generating reports."""
    
    def __init__(self, thread_id: str = None, thread_manager: Optional[ThreadManager] = None, project_id: str = None):
        super().__init__()
        self.thread_id = thread_id
        self.thread_manager = thread_manager
        self.project_id = project_id
        
        # Initialize todo generator if we have the necessary parameters
        self.todo_generator = None
        if project_id and thread_manager:
            try:
                from agent.tools.todo_generator_tool import TodoGeneratorTool
                self.todo_generator = TodoGeneratorTool(project_id=project_id, thread_manager=thread_manager)
                logger.info("TodoGeneratorTool initialized for MarketResearchTool")
            except Exception as e:
                logger.error(f"Failed to initialize TodoGeneratorTool: {str(e)}")
                traceback.print_exc()
    
    @openapi_schema({
        "type": "function",
        "function": {
            "name": "conduct_market_research",
            "description": "Conduct comprehensive market research on an industry or market segment, identifying key players, market sizes, strengths, weaknesses, and trends. The results will be structured for further analysis or report generation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "industry": {
                        "type": "string",
                        "description": "The industry or market segment to research (e.g., 'healthcare in the UK', 'electric vehicles in Germany')"
                    },
                    "num_companies": {
                        "type": "integer",
                        "description": "Number of top companies to include in the research (default: 5)",
                        "default": 5
                    },
                    "include_market_size": {
                        "type": "boolean",
                        "description": "Whether to include market size estimates in the research",
                        "default": true
                    },
                    "include_trends": {
                        "type": "boolean",
                        "description": "Whether to include market trends in the research",
                        "default": true
                    }
                },
                "required": ["industry"]
            }
        }
    })
    @xml_schema(
        tag_name="conduct-market-research",
        mappings=[
            {"param_name": "industry", "node_type": "content", "path": "."},
            {"param_name": "num_companies", "node_type": "attribute", "path": ".", "required": False},
            {"param_name": "include_market_size", "node_type": "attribute", "path": ".", "required": False},
            {"param_name": "include_trends", "node_type": "attribute", "path": ".", "required": False}
        ],
        example='''
        <!-- Conduct comprehensive market research on an industry -->
        
        <conduct-market-research num_companies="5" include_market_size="true" include_trends="true">
        healthcare in the UK
        </conduct-market-research>
        '''
    )
    async def conduct_market_research(self, 
                                     industry: str, 
                                     num_companies: int = 5, 
                                     include_market_size: bool = True, 
                                     include_trends: bool = True) -> ToolResult:
        """
        Conduct comprehensive market research on an industry.
        
        Args:
            industry: The industry or market segment to research
            num_companies: Number of top companies to include
            include_market_size: Whether to include market size estimates
            include_trends: Whether to include market trends
            
        Returns:
            ToolResult containing the structured market research data
        """
        try:
            logger.info(f"Starting market research for: {industry}")
            
            # First, ensure a todo list is created for this market research task
            todo_created = False
            if self.todo_generator:
                try:
                    # Create a task description that includes the industry
                    task_description = f"Market research for {industry}"
                    # Ensure the todo list exists and is up to date
                    todo_result = await self.todo_generator.ensure_todo_exists(task_description=task_description, overwrite=True)
                    logger.info(f"Todo list creation result: {todo_result.message}")
                    todo_created = True
                except Exception as e:
                    logger.error(f"Error creating todo list: {str(e)}")
                    # Continue with market research even if todo creation fails
            else:
                # If todo_generator is not available, try to create it now
                logger.warning("TodoGeneratorTool not initialized, attempting to create it now")
                try:
                    from agent.tools.todo_generator_tool import TodoGeneratorTool
                    if self.project_id and self.thread_manager:
                        self.todo_generator = TodoGeneratorTool(project_id=self.project_id, thread_manager=self.thread_manager)
                        # Try again to create the todo list
                        task_description = f"Market research for {industry}"
                        todo_result = await self.todo_generator.ensure_todo_exists(task_description=task_description, overwrite=True)
                        logger.info(f"Todo list creation result (retry): {todo_result.message}")
                        todo_created = True
                except Exception as e:
                    logger.error(f"Failed to initialize TodoGeneratorTool on retry: {str(e)}")
                    traceback.print_exc()
            
            # Create a structured research plan
            research_plan = {
                "industry": industry,
                "num_companies": num_companies,
                "include_market_size": include_market_size,
                "include_trends": include_trends,
                "research_steps": [
                    "1. Gather industry overview and market size data",
                    "2. Identify top companies in the industry",
                    "3. Research each company's profile, strengths, and weaknesses",
                    "4. Analyze market trends and growth projections",
                    "5. Compile findings into structured data"
                ]
            }
            
            # Log the research plan
            logger.info(f"Market research plan created: {json.dumps(research_plan)}")
            
            # Remind the user to check the todo list
            if todo_created:
                research_plan["todo_list_created"] = True
                research_plan["note"] = "IMPORTANT: A detailed todo list has been created to guide this market research task. Please check the todo.md file for the structured plan."
                # Add the todo list as the first step in the research steps
                research_plan["research_steps"].insert(0, "0. Review the generated todo.md file for a detailed research plan")
            else:
                research_plan["todo_list_created"] = False
                research_plan["note"] = "Note: Could not create a todo list. Please manually create a structured plan for this research task."
            
            # Return the research plan to guide the agent's research process
            return self.success_response({
                "status": "research_plan_created",
                "message": "Market research plan created. The agent should now execute this plan using web search, browser navigation, and data collection tools.",
                "research_plan": research_plan,
                "next_steps": [
                    "Use web_search to gather industry overview and market size data",
                    "Use web_search to identify top companies in the industry",
                    "For each company, use web_search or browser_navigate_to to gather detailed information",
                    "Compile findings into a structured format",
                    "Use generate_pdf to create a comprehensive market research report"
                ]
            })
            
        except Exception as e:
            logger.error(f"Error conducting market research: {str(e)}")
            logger.debug(traceback.format_exc())
            return self.fail_response(f"Error conducting market research: {str(e)}")
            
    @openapi_schema({
        "type": "function",
        "function": {
            "name": "generate_market_report",
            "description": "Generate a comprehensive market research report based on collected data about companies and market trends. The report will be formatted as a PDF.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Title of the market research report"
                    },
                    "industry_overview": {
                        "type": "string",
                        "description": "Overview of the industry including market size and structure"
                    },
                    "companies": {
                        "type": "array",
                        "description": "Array of company profiles to include in the report",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "Company name"},
                                "website": {"type": "string", "description": "Company website URL"},
                                "market_cap": {"type": "string", "description": "Market capitalization or company size"},
                                "revenue": {"type": "string", "description": "Annual revenue"},
                                "strengths": {"type": "string", "description": "Company strengths"},
                                "weaknesses": {"type": "string", "description": "Company weaknesses"}
                            },
                            "required": ["name"]
                        }
                    },
                    "trends": {
                        "type": "string",
                        "description": "Market trends and growth projections"
                    },
                    "filename": {
                        "type": "string",
                        "description": "Filename for the PDF report (default: market_research_report.pdf)",
                        "default": "market_research_report.pdf"
                    }
                },
                "required": ["title", "companies"]
            }
        }
    })
    @xml_schema(
        tag_name="generate-market-report",
        mappings=[
            {"param_name": "title", "node_type": "attribute", "path": "."},
            {"param_name": "industry_overview", "node_type": "content", "path": "industry_overview"},
            {"param_name": "companies", "node_type": "content", "path": "companies"},
            {"param_name": "trends", "node_type": "content", "path": "trends"},
            {"param_name": "filename", "node_type": "attribute", "path": ".", "required": False}
        ],
        example='''
        <!-- Generate a comprehensive market research report -->
        
        <generate-market-report title="UK Healthcare Market Analysis" filename="uk_healthcare_market_report.pdf">
            <industry_overview>
            The UK healthcare market is valued at approximately £200 billion and consists of both public (NHS) and private healthcare providers. The market has been growing at a rate of 2.5% annually over the past five years.
            </industry_overview>
            
            <companies>
            [
                {
                    "name": "NHS England",
                    "website": "https://www.england.nhs.uk/",
                    "market_cap": "Public entity",
                    "revenue": "£130 billion annual budget",
                    "strengths": "Universal coverage, extensive infrastructure, trusted brand",
                    "weaknesses": "Budget constraints, long waiting times, bureaucratic processes"
                },
                {
                    "name": "Bupa",
                    "website": "https://www.bupa.co.uk/",
                    "market_cap": "£3.7 billion",
                    "revenue": "£12.9 billion",
                    "strengths": "Strong brand recognition, diverse service offerings, international presence",
                    "weaknesses": "High premium costs, limited coverage in some regions"
                }
            ]
            </companies>
            
            <trends>
            Key trends in the UK healthcare market include increasing digitalization of healthcare services, growing demand for mental health services, and rising interest in preventative care and wellness programs. The market is expected to grow at a CAGR of 3.7% over the next five years.
            </trends>
        </generate-market-report>
        '''
    )
    async def generate_market_report(self, 
                                    title: str, 
                                    companies: List[Dict[str, Any]], 
                                    industry_overview: str = "", 
                                    trends: str = "", 
                                    filename: str = "market_research_report.pdf") -> ToolResult:
        """
        Generate a comprehensive market research report.
        
        Args:
            title: Title of the market research report
            companies: Array of company profiles
            industry_overview: Overview of the industry
            trends: Market trends and growth projections
            filename: Filename for the PDF report
            
        Returns:
            ToolResult containing the path to the generated PDF report
        """
        try:
            logger.info(f"Generating market research report: {title}")
            
            # Format the report content in markdown
            report_content = f"# {title}\n\n"
            
            # Add industry overview section
            if industry_overview:
                report_content += "## Industry Overview\n\n"
                report_content += f"{industry_overview}\n\n"
            
            # Add companies section
            report_content += "## Major Players\n\n"
            for company in companies:
                report_content += f"### {company.get('name', 'Unnamed Company')}\n\n"
                
                if 'website' in company:
                    report_content += f"**Website**: [{company['website']}]({company['website']})\n\n"
                
                if 'market_cap' in company:
                    report_content += f"**Market Cap**: {company['market_cap']}\n\n"
                
                if 'revenue' in company:
                    report_content += f"**Revenue**: {company['revenue']}\n\n"
                
                if 'strengths' in company:
                    report_content += "**Strengths**:\n"
                    for strength in company['strengths'].split(','):
                        report_content += f"- {strength.strip()}\n"
                    report_content += "\n"
                
                if 'weaknesses' in company:
                    report_content += "**Weaknesses**:\n"
                    for weakness in company['weaknesses'].split(','):
                        report_content += f"- {weakness.strip()}\n"
                    report_content += "\n"
            
            # Add trends section
            if trends:
                report_content += "## Market Trends and Growth Projections\n\n"
                report_content += f"{trends}\n\n"
            
            # Add conclusion
            report_content += "## Conclusion\n\n"
            report_content += "This market research report provides a comprehensive overview of the industry, "
            report_content += "major players, and market trends. The information can be used to inform strategic "
            report_content += "decisions and identify opportunities for growth and investment.\n"
            
            # Log the report content (truncated for log size)
            logger.info(f"Market report content created: {report_content[:500]}...")
            
            # Return the report content for the agent to use with the PDF generation tool
            return self.success_response({
                "status": "report_content_created",
                "message": "Market research report content created. Use the generate_pdf tool to create the final PDF report.",
                "report_title": title,
                "report_content": report_content,
                "suggested_filename": filename,
                "next_step": "Use generate_pdf tool with this content to create the final PDF report"
            })
            
        except Exception as e:
            logger.error(f"Error generating market report: {str(e)}")
            logger.debug(traceback.format_exc())
            return self.fail_response(f"Error generating market report: {str(e)}")


# Register this tool with the agent
def register_market_research_tool(thread_manager, thread_id):
    """Register the market research tool with the agent."""
    try:
        thread_manager.add_tool(
            MarketResearchTool,
            thread_id=thread_id,
            thread_manager=thread_manager
        )
        logger.info("Market research tool registered successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to register market research tool: {str(e)}")
        return False
