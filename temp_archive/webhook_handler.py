"""
Responsible for orchestrating tasks from the Notion webhook to the manager agent.
"""

from typing import Any, Dict, Optional, Tuple
from fastapi import HTTPException
from .notion_api import NotionAPI
import logging
from openai import OpenAI
import os
from crews.research_crew.crew import ResearchCrew

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def determine_crew(task_content: str) -> str | None:
    """
    Use LLM to determine which crew should handle the task.
    
    Args:
        task_content: The content of the task to be processed
        
    Returns:
        str: The name of the crew to use, or None for default processing
    """
    try:
        system_prompt = """You are a task routing expert. Your job is to determine if a task requires a specialized crew.
        Available crews:
        - 'research': For in-depth research, analysis, and investigation tasks that require gathering information from multiple sources, analyzing trends, or providing comprehensive reports.
        - None: For simple tasks that don't require specialized handling, such as answering basic questions or providing brief information.
        
        Respond with ONLY the single word 'research' (no quotes, no punctuation) if the task requires research crew, or the single word 'none' (no quotes) for simple tasks."""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Task: {task_content}"}
            ],
            temperature=0.1,
            max_tokens=10
        )
        
        result = response.choices[0].message.content.strip().lower()
        logger.info(f"LLM response for crew determination: '{result}'")
        
        # Check if SERPER_API_KEY is available for research crew
        if result == 'research' and not os.getenv('SERPER_API_KEY'):
            logger.warning("SERPER_API_KEY not found. Research crew requires this API key.")
            return None
            
        return 'research' if 'research' in result else None
        
    except Exception as e:
        logger.error(f"Error in crew determination: {str(e)}")
        return None

async def process_task_with_crew(task_content: str, crew_type: str) -> tuple[str, str | None]:
    """
    Process a task using the specified crew.
    
    Args:
        task_content: The content of the task to be processed
        crew_type: The type of crew to use
        
    Returns:
        tuple: (response_text, thought_process)
    """
            thought_process = []
            
            def capture_thought(output):
                try:
                    if hasattr(output, 'output'):
                        thought_process.append(f"Step {len(thought_process) + 1}: {output.output}\n")
                    elif hasattr(output, 'result'):
                        thought_process.append(f"Tool result: {output.result}\n")
                    elif hasattr(output, 'content'):
                        thought_process.append(f"Content: {output.content}\n")
                    else:
                        thought_process.append(f"Tool used: {str(output)}\n")
                except Exception as e:
                    thought_process.append(f"Error capturing thought: {str(e)}\n")
            
    if crew_type == 'research':
        logger.info("Using Research Crew for this task...")
            try:
                crew = ResearchCrew()
                crew.researcher().step_callback = capture_thought
                crew.senior_researcher().step_callback = capture_thought
                
                # Check if tools are properly initialized
                if not crew.researcher().tools:
                logger.warning("No tools available for researcher. Using default processing instead.")
                    raise Exception("No tools available")
                    
                result = crew.crew().kickoff(inputs={'topic': task_content})
                return result.raw, "\n".join(thought_process)
            except Exception as e:
            logger.error(f"Error using Research Crew: {str(e)}")
            logger.info("Falling back to default OpenAI processing...")
        
        # Default OpenAI processing
    logger.info("Using default OpenAI processing...")
    response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Provide clear, concise responses."},
                {"role": "user", "content": task_content}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        return response.choices[0].message.content, None
        
async def process_task(task_content: str) -> tuple[str, str | None]:
    """
    Main function to process a task through the orchestrator.
    
    Args:
        task_content: The content of the task to be processed
    
    Returns:
        tuple: (response_text, thought_process)
    """
    try:
        logger.info(f"Processing task: {task_content}")
            
            # Determine which crew to use
            crew_type = await determine_crew(task_content)
            
        # Process the task with the appropriate crew
            response_text, thought_process = await process_task_with_crew(task_content, crew_type)
            
        return response_text, thought_process
        
    except Exception as e:
        logger.error(f"Error processing task: {str(e)}")
        return f"Error processing task: {str(e)}", None

async def process_notion_webhook(payload: dict, notion_api) -> dict:
    """
    Process a webhook payload from Notion.
    
    Args:
        payload: The webhook payload from Notion
        notion_api: The NotionAPI instance
        
    Returns:
        dict: A summary of the processing result
    """
    # This function would handle webhook events if you decide to use webhooks in the future
    # For now, it's a placeholder since you're using scheduled polling
    return {"message": "Webhook received but not processed - using scheduled polling instead"}