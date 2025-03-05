"""
Implements logic for choosing which crew should handle the task.
Routes tasks to appropriate crews based on task properties and content analysis.
"""

from typing import Dict, Any, Tuple, Optional
import importlib
import os
from dotenv import load_dotenv

load_dotenv()

class TaskRouter:
    """
    Routes tasks to appropriate crews based on task content and tags.
    Crews are implemented separately in the crews/ directory.
    """
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
    def _determine_crew(self, task_details: Dict[str, Any]) -> str:
        """
        Determine appropriate crew based on task details and manual tags.
        
        Args:
            task_details (Dict[str, Any]): Task information from Notion
            
        Returns:
            str: Identifier for the selected crew
        """
        # Check manual tag first
        manual_tag = task_details.get("properties", {}).get("Manual Tag", {}).get("select", {}).get("name", "").lower()
        
        if manual_tag:
            if "analysis" in manual_tag:
                return "analysis_crew"
            elif "content" in manual_tag or "writing" in manual_tag:
                return "content_crew"
            elif "dev" in manual_tag or "code" in manual_tag:
                return "dev_crew"
        
        # Analyze title and description
        title = task_details.get("properties", {}).get("Title", {}).get("title", [{}])[0].get("text", {}).get("content", "").lower()
        description = task_details.get("properties", {}).get("Description", {}).get("rich_text", [{}])[0].get("text", {}).get("content", "").lower()
        
        # Keyword-based classification
        analysis_keywords = ["analyze", "data", "metrics", "statistics", "report", "research"]
        content_keywords = ["write", "content", "summary", "article", "blog", "document"]
        
        if any(keyword in title + " " + description for keyword in analysis_keywords):
            return "analysis_crew"
        elif any(keyword in title + " " + description for keyword in content_keywords):
            return "content_crew"
        
        return "dev_crew"  # default crew
    
    async def _call_crew(self, crew_identifier: str, task_details: Dict[str, Any]) -> Any:
        """
        Dynamically imports and calls the appropriate crew's process method.
        
        Args:
            crew_identifier (str): The crew module to import (e.g., "analysis_crew")
            task_details (Dict[str, Any]): Task information to pass to the crew
            
        Returns:
            Any: The crew's processing result
        """
        try:
            # Import the crew module dynamically
            crew_module = importlib.import_module(f"crews.{crew_identifier}")
            return await crew_module.process(task_details)
        except ImportError as e:
            return {"error": f"Crew module {crew_identifier} not found: {str(e)}"}
        except Exception as e:
            return {"error": f"Error processing with {crew_identifier}: {str(e)}"}
    
    async def route_and_execute_task(self, task_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Routes task to appropriate crew and executes it.
        
        Args:
            task_details (Dict[str, Any]): Task information from Notion
            
        Returns:
            Dict[str, Any]: Execution results including summary and crew used
        """
        # Determine which crew should handle this task
        selected_crew = self._determine_crew(task_details)
        
        # Execute the task with the selected crew
        result = await self._call_crew(selected_crew, task_details)
        
        return {
            "crew": selected_crew,
            "result": result
        }