"""
Manages the selection and execution of specialized crews for task processing.
"""

import logging
import os
from typing import Tuple, Optional, List, Dict, Any
from openai import AsyncOpenAI
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from crews.research_crew.crew import ResearchCrew
import traceback

logger = logging.getLogger(__name__)

class CrewManager:
    """
    Manages the selection and execution of specialized crews for task processing.
    
    This class:
    1. Determines which crew should handle a task
    2. Initializes and runs the appropriate crew
    3. Falls back to default processing when needed
    """
    
    def __init__(self):
        """Initialize the CrewManager."""
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.serper_api_key = os.getenv("SERPER_API_KEY")
        self.llm = ChatOpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
            model="gpt-4o-mini",
            temperature=0
        )
        # Add a list to store thought process
        self.thought_process = []
    
    def callback_function(self, output):
        """Callback function to track agent's thought process"""
        try:
            if hasattr(output, 'output'):
                thought_entry = f"Task completed!\nOutput: {output.output}\n"
            elif hasattr(output, 'result'):
                thought_entry = f"Tool result: {output.result}\n"
            elif hasattr(output, 'content'):
                thought_entry = f"Content: {output.content}\n"
            else:
                thought_entry = f"Tool used: {str(output)}\n"
            
            # Limit the length of very long outputs to prevent Notion API issues
            if len(thought_entry) > 10000:
                logger.warning(f"Truncating very long thought entry ({len(thought_entry)} chars)")
                thought_entry = thought_entry[:10000] + "... [truncated due to length]"
            
            # Add to thought process list
            self.thought_process.append(thought_entry)
            # Also log for debugging
            logger.debug(f"Thought process entry added ({len(thought_entry)} chars)")
        except Exception as e:
            error_entry = f"Error capturing thought: {str(e)}\n"
            self.thought_process.append(error_entry)
            logger.error(error_entry)
    
    async def determine_crew(self, task_content: str) -> Tuple[str, str]:
        """Determine which crew should handle this task."""
        # Clear thought process for new task
        self.thought_process = []
        
        system_prompt = """
        You are a task router that determines which specialized crew should handle a given task.
            Available crews:
        - research_crew: For tasks requiring web research, information gathering, and synthesis
        - default: For general tasks that don't fit other specialized crews
        
        Respond with ONLY the crew name followed by a brief explanation, like this:
        research_crew: This task requires gathering information from multiple sources
        OR
        default: This is a general task that doesn't require specialized handling
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Task: {task_content}")
        ]
        
        response = self.llm.invoke(messages).content.strip()
        
        # Parse the response
        try:
            crew_name, reasoning = response.split(":", 1)
            crew_name = crew_name.strip().lower()
            reasoning = reasoning.strip()
            
            # Validate crew name
            if crew_name not in ["research_crew", "default"]:
                logger.warning(f"Invalid crew name: {crew_name}. Falling back to default.")
                crew_name = "default"
                reasoning = "Fallback due to invalid crew determination."
            
            return crew_name, reasoning
            
        except Exception as e:
            logger.error(f"Error parsing crew determination: {str(e)}")
            return "default", "Fallback due to error in crew determination."
    
    async def process_with_crew(self, crew_name: str, task_content: str) -> Tuple[str, str]:
        """Process the task with the appropriate crew."""
        logger.debug(f"Starting process_with_crew with crew_name={crew_name}")
        self.thought_process = []  # Reset thought process
        
        if crew_name == "research_crew":
            try:
                logger.debug("Initializing ResearchCrew")
                crew = ResearchCrew()
                
                # Set callbacks for both agents
                researcher = crew.researcher()
                researcher.step_callback = self.callback_function
                
                senior_researcher = crew.senior_researcher()
                senior_researcher.step_callback = self.callback_function
                
                # This is a synchronous call - don't use await
                logger.debug("Starting crew.kickoff()")
                result = crew.crew().kickoff(inputs={'topic': task_content})
                logger.debug(f"crew.kickoff() completed, result type: {type(result)}")
                
                # Extract result text
                if hasattr(result, 'raw'):
                    result_text = result.raw
                    logger.debug(f"Extracted raw result, length: {len(result_text)}")
                else:
                    result_text = str(result)
                    logger.debug(f"Converted result to string, length: {len(result_text)}")
                
                # Join thought process entries
                thought_process_text = "\n".join(self.thought_process)
                logger.debug(f"Joined thought process, length: {len(thought_process_text)}")
                
                logger.debug("Returning results from process_with_crew")
                return result_text, thought_process_text
            except Exception as e:
                logger.error(f"Error with research crew: {str(e)}")
                logger.error(traceback.format_exc())
                # Fall back to default processing
                logger.debug("Falling back to default processing")
                return await self._process_with_default(task_content)
        else:
            logger.debug("Using default processing")
            return await self._process_with_default(task_content)
    
    async def _process_with_default(self, task_content: str) -> Tuple[str, str]:
        """Process the task with the default OpenAI processing."""
        messages = [
            SystemMessage(content="You are a helpful assistant that processes tasks."),
            HumanMessage(content=f"Task: {task_content}")
        ]
        
        response = self.llm.invoke(messages).content.strip()
        
        # For default processing, we don't have detailed thought process
        default_thought = "Processed with default OpenAI processing (no detailed thought process available)"
        
        return response, default_thought
    
    async def process_task(self, task_content: str, task_id: str) -> Tuple[str, Optional[str]]:
        """Process a task using the appropriate crew or default processing"""
        try:
            # Determine which crew should handle the task
            crew_type = await self.determine_crew(task_content)
            
            if crew_type[0] == "research_crew":
                logger.info(f"Using Research Crew for task {task_id}")
                return await self.process_with_crew(crew_type[0], task_content)
            else:
                logger.info(f"Using default processing for task {task_id}")
                return await self._process_with_default(task_content)
        except Exception as e:
            logger.error(f"Error in process_task: {str(e)}")
            raise
    
    async def process_with_research_crew(self, task_content: str, task_id: str) -> Tuple[str, str]:
        """Process the task with the research crew."""
        # Implementation of process_with_research_crew method
        pass
    
    async def process_with_default(self, task_content: str) -> Tuple[str, str]:
        """Process the task with the default OpenAI processing."""
        messages = [
            SystemMessage(content="You are a helpful assistant that processes tasks."),
            HumanMessage(content=f"Task: {task_content}")
        ]
        
        response = self.llm.invoke(messages).content.strip()
        
        # For default processing, we don't have detailed thought process
        default_thought = "Processed with default OpenAI processing (no detailed thought process available)"
        
        return response, default_thought 