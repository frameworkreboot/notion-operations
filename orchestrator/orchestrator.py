"""
Core orchestration logic for processing tasks from Notion.
"""

import logging
import os
from typing import Tuple, Optional, List, Dict, Any

from .notion_api import NotionAPI
from .crew_manager import CrewManager

logger = logging.getLogger(__name__)

class TaskOrchestrator:
    """
    Orchestrates the processing of tasks from Notion.
    
    This class:
    1. Retrieves tasks from Notion
    2. Determines which crew should handle each task
    3. Processes tasks with the appropriate crew
    4. Updates Notion with the results
    """
    
    def __init__(self):
        """Initialize the TaskOrchestrator with required components."""
        self.notion_api = NotionAPI(
            notion_api_key=os.getenv("NOTION_API_KEY"),
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        self.crew_manager = CrewManager()
    
    async def process_execute_tasks(self) -> List[Dict[str, Any]]:
        """
        Poll for tasks with 'Execute' status and process them.
        
        This function:
        1. Queries the Notion database for tasks with 'Execute' status
        2. Updates each task's status to 'In progress'
        3. Processes the task content using the appropriate crew
        4. Updates the task with the results and changes status to 'Review'
        """
        try:
            logger.info("Checking for tasks with 'Execute' status...")
            tasks = await self.notion_api.query_tasks_to_execute()
            
            if not tasks or 'results' not in tasks:
                logger.info("No 'Execute' tasks found")
                return []
                
            logger.info(f"Found {len(tasks['results'])} tasks to process")
            
            results = []
            for task in tasks['results']:
                try:
                    page_id = task['id']
                    task_content = task['properties']['Task']['title'][0]['text']['content']
                    logger.info(f"Processing 'Execute' task: {task_content}")
                    
                    # Update status to In Progress
                    logger.debug(f"Updating task {page_id} status to 'In progress'")
                    await self.notion_api.update_task_status(page_id, "In progress")
                    
                    # Process the task with the appropriate crew
                    logger.debug(f"Calling crew_manager.process_task for {page_id}")
                    result = await self.crew_manager.process_task(task_content, page_id)
                    logger.debug(f"crew_manager.process_task returned result type: {type(result)}")
                    
                    # Check if result is a tuple with response and thought process
                    if isinstance(result, tuple) and len(result) >= 2:
                        response_text, thought_process = result
                        logger.debug(f"Got response (length: {len(response_text)}) and thought process (length: {len(thought_process) if thought_process else 0})")
                        
                        # Update Notion with the results
                        logger.debug(f"Updating Notion with results for {page_id}")
                        await self._update_notion_with_results(page_id, response_text, thought_process)
                        logger.debug(f"Notion update completed for {page_id}")
                    else:
                        logger.warning(f"Unexpected result format from process_task: {result}")
                    
                    results.append(result)
                    logger.info(f"Successfully processed task: {task_content}")
                    
                except Exception as e:
                    logger.error(f"Error processing task {page_id}: {str(e)}")
                    logger.error(traceback.format_exc())
                    await self.notion_api.create_error_log(page_id, str(e))
                    continue
                    
            return results
        except Exception as e:
            logger.error(f"Error processing tasks: {str(e)}")
            logger.error(traceback.format_exc())
            return []
    
    async def process_iteration_tasks(self) -> List[Dict[str, Any]]:
        """
        Poll for tasks with 'Iterate' status and process them with feedback.
        
        This function:
        1. Queries the Notion database for tasks with 'Iterate' status
        2. Retrieves comments from the page
        3. Processes the task with comments as feedback
        4. Updates the task with new results
        """
        try:
            logger.info("Checking for tasks with 'Iterate' status...")
            tasks = await self.notion_api.query_tasks_to_iterate()
            
            if not tasks or 'results' not in tasks:
                logger.info("No 'Iteration' tasks found")
                return []
                
            logger.info(f"Found {len(tasks['results'])} tasks to iterate")
            
            results = []
            for task in tasks['results']:
                try:
                    page_id = task['id']
                    task_title = task['properties']['Task']['title'][0]['text']['content']
                    logger.info(f"Processing 'Iteration' task: {task_title}")
                    
                    # Update status to In Progress
                    await self.notion_api.update_task_status(page_id, "In progress")
                    
                    # Get comments from the page
                    comments = await self.notion_api.get_page_comments(page_id)
                    
                    if comments:
                        logger.info(f"Found {len(comments)} comments for iteration")
                        
                        # Process the task with comments as feedback
                        feedback_prompt = f"Original task: {task_title}\n\nFeedback comments:\n"
                        for comment in comments:
                            feedback_prompt += f"- {comment}\n"
                        
                        result = await self.crew_manager.process_iteration(feedback_prompt, page_id, comments)
                        results.append(result)
                        
                        logger.info(f"Successfully processed iteration for task: {task_title}")
                    else:
                        logger.warning(f"No comments found for iteration on task: {task_title}")
                        await self.notion_api.update_task_status(page_id, "Review")
                    
                except Exception as e:
                    logger.error(f"Error processing iteration task {page_id}: {str(e)}")
                    await self.notion_api.create_error_log(page_id, str(e))
                    continue
                    
            return results
        except Exception as e:
            logger.error(f"Error processing iteration tasks: {str(e)}")
            return []
    
    async def _update_notion_with_results(
        self, 
        page_id: str, 
        response_text: str, 
        thought_process: Optional[str] = None,
        is_iteration: bool = False
    ) -> None:
        """
        Update a Notion page with task processing results.
        
        Args:
            page_id: The Notion page ID
            response_text: The response text to add
            thought_process: Optional thought process to include
            is_iteration: Whether this is an iteration update
        """
        # Update status and summary
        await self.notion_api.update_task_status(
            page_id=page_id,
            status="Review",
            summary=response_text[:2000]
        )
        
        # Create blocks for page content
        blocks = []
        
        # Add AI Response section
        response_title = "AI Response (Iteration)" if is_iteration else "AI Response"
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": response_title}}]
            }
        })
        
        # Add response content in chunks
        for i in range(0, len(response_text), 2000):
            chunk = response_text[i:i+2000]
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": chunk}}]
                }
            })
        
        # Add thought process if available
        if thought_process:
            blocks.append({
                "object": "block",
                "type": "divider",
                "divider": {}
            })
            
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "Thought Process"}}]
                }
            })
            
            for i in range(0, len(thought_process), 2000):
                chunk = thought_process[i:i+2000]
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": chunk}}]
                    }
                })
        
        # Update the page content
        await self.notion_api.update_page_content(page_id, blocks)

    async def process_task(self, task: Dict[str, Any]):
        """Process a single task."""
        page_id = task["id"]
        
        try:
            # Update status to In Progress
            await self.notion_api.update_task_status(page_id, "In Progress")
            
            # Extract task content
            task_content = self._extract_task_content(task)
            
            # Determine which crew should handle this task
            crew_name, crew_reasoning = await self.crew_manager.determine_crew(task_content)
            
            # Process the task with the appropriate crew
            # This is now a synchronous call - don't await it
            result_text, thought_process = self.crew_manager.process_with_crew(crew_name, task_content)
            
            # Update the task with the result
            await self.notion_api.update_task_response(page_id, result_text)
            
            # Update the page content with more detailed information
            content = f"Task processed by: {crew_name}\n\nReasoning: {crew_reasoning}\n\nResult:\n{result_text}"
            await self.notion_api.update_page_content(page_id, content, thought_process)
            
            # Update status to Done
            await self.notion_api.update_task_status(page_id, "Done")
            
            logger.info(f"Successfully processed task {page_id}")
            
        except Exception as e:
            logger.error(f"Error processing task {page_id}: {str(e)}")
            # Update status to indicate error - use a valid status
            await self.notion_api.update_task_response(page_id, f"Error: {str(e)}")
            await self.notion_api.update_task_status(page_id, "Review")  # Use a valid status like Review

    # Add this debug method to help isolate the issue
    async def debug_api_connection(self):
        """Test the connection to the Notion API"""
        logger.debug("Testing Notion API connection...")
        try:
            # Try a simple API call
            database = await self.notion_api.client.databases.retrieve(database_id=self.notion_api.database_id)
            logger.debug(f"Successfully connected to database: {database.get('title', [{'plain_text': 'Unknown'}])[0]['plain_text']}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Notion API: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    # Update the test_flow function to call this first
    async def test_flow(self):
        """Test function to manually trigger the scheduled service flow once"""
        logger.info("Starting manual test of Notion task processor...")
        
        # Initialize the orchestrator
        orchestrator = TaskOrchestrator()
        
        # Test API connection first
        api_ok = await orchestrator.debug_api_connection()
        if not api_ok:
            logger.error("Notion API connection test failed, aborting test")
            return
        
        # Rest of the function...
