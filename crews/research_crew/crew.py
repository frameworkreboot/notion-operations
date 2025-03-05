from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import (
	SerperDevTool,
	WebsiteSearchTool,
	ScrapeWebsiteTool
)
from pydantic import BaseModel, Field
from typing import List, Dict

class InitialResearchOutput(BaseModel):
    """Output model for initial research task"""
    key_facts: List[str] = Field(..., description="Key facts and data points discovered")
    recent_developments: List[str] = Field(..., description="Recent developments in the topic")
    expert_opinions: List[Dict[str, str]] = Field(..., description="Expert opinions with source attribution")
    statistics: List[Dict[str, str]] = Field(..., description="Relevant statistics with source attribution")
    sources: List[str] = Field(..., description="List of sources consulted")

class ResearchOutput(BaseModel):
    """Output model for final research analysis"""
    executive_summary: str = Field(..., description="Brief overview of the entire analysis")
    initial_research: InitialResearchOutput = Field(..., description="Raw research findings")
    key_findings: List[str] = Field(..., description="Key findings from the analysis")
    trend_analysis: Dict[str, str] = Field(..., description="Analysis of identified trends")
    recommendations: List[str] = Field(..., description="Actionable recommendations based on the research")

def callback_function(output):
    """Callback function to track agent's thought process"""
    try:
        if hasattr(output, 'output'):
            output_text = f"\nTask completed!\nOutput: {output.output}\n"
        elif hasattr(output, 'result'):
            output_text = f"\nTool result: {output.result}\n"
        elif hasattr(output, 'content'):
            output_text = f"\nContent: {output.content}\n"
        else:
            output_text = f"\nTool used: {str(output)}\n"
        
        # Limit the length of very long outputs
        if len(output_text) > 5000:
            output_text = output_text[:5000] + "... [truncated]"
            
        print(output_text)
    except Exception as e:
        print(f"Error in callback_function: {str(e)}")

@CrewBase
class ResearchCrew:
    """Research crew for analyzing topics"""

    @agent
    def researcher(self) -> Agent:
        # Initialize tools with proper error handling
        try:
            search_tool = SerperDevTool()
            website_search_tool = WebsiteSearchTool()
            scrape_tool = ScrapeWebsiteTool()
            
            tools = [search_tool, website_search_tool, scrape_tool]
        except Exception as e:
            print(f"Error initializing tools: {str(e)}")
            # Fallback to simpler tools if needed
            tools = []
        
        return Agent(
            config=self.agents_config['researcher'],
            step_callback=callback_function,
            output_pydantic=InitialResearchOutput,
            tools=tools,
            verbose=True
        )

    @agent
    def senior_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['senior_researcher'],
            step_callback=callback_function,
            output_pydantic=ResearchOutput,
            verbose=True
        )

    @task
    def initial_research(self) -> Task:
        return Task(
            config=self.tasks_config['initial_research']
        )

    @task
    def analysis_and_synthesis(self) -> Task:
        return Task(
            config=self.tasks_config['analysis_and_synthesis'],
            output_file='output/final_analysis.md'
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Research crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        ) 