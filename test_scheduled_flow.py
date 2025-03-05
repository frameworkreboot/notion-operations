import asyncio
import logging
import sys
import traceback
from dotenv import load_dotenv
from orchestrator.orchestrator import TaskOrchestrator

# Configure logging - increase level to DEBUG and ensure it goes to console
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # Ensure logs go to stdout
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def test_flow():
    """Test function to manually trigger the scheduled service flow once"""
    logger.info("Starting manual test of Notion task processor...")
    
    # Initialize the orchestrator
    logger.debug("Initializing TaskOrchestrator...")
    orchestrator = TaskOrchestrator()
    logger.debug("TaskOrchestrator initialized successfully")
    
    # Add a simple test to verify Notion API connection
    logger.debug("Testing Notion API connection...")
    try:
        # Test updating a known page
        test_page_id = "1adee1580432800c9f4bd5753d76e06d"  # Use the same page ID that worked in test_notion_update.py
        await orchestrator.notion_api.update_task_status(test_page_id, "In progress")
        logger.debug("Notion API connection test successful")
    except Exception as e:
        logger.error(f"Notion API connection test failed: {str(e)}")
        logger.error(traceback.format_exc())
        return  # Exit if we can't connect to Notion
    
    try:
        # Process tasks with step-by-step logging
        logger.info("Processing 'Execute' tasks...")
        
        # Step 1: Query tasks
        logger.debug("Step 1: Querying for 'Execute' tasks...")
        tasks = await orchestrator.notion_api.query_tasks_to_execute()
        if not tasks or 'results' not in tasks:
            logger.info("No 'Execute' tasks found")
        else:
            logger.info(f"Found {len(tasks['results'])} tasks with 'Execute' status")
            
            # Step 2: Process each task individually with detailed logging
            for i, task in enumerate(tasks['results']):
                try:
                    page_id = task['id']
                    task_content = task['properties']['Task']['title'][0]['text']['content']
                    logger.info(f"Processing task {i+1}/{len(tasks['results'])}: {task_content[:50]}...")
                    
                    # Step 2.1: Update status to In Progress
                    logger.debug(f"Step 2.1: Updating task {page_id} status to 'In progress'")
                    await orchestrator.notion_api.update_task_status(page_id, "In progress")
                    
                    # Step 2.2: Determine crew
                    logger.debug(f"Step 2.2: Determining crew for task {page_id}")
                    crew_type = await orchestrator.crew_manager.determine_crew(task_content)
                    logger.debug(f"Crew determination result: {crew_type}")
                    
                    # Step 2.3: Process with appropriate crew
                    logger.debug(f"Step 2.3: Processing task with {crew_type[0]} crew")
                    result = await orchestrator.crew_manager.process_task(task_content, page_id)
                    logger.debug(f"Processing result type: {type(result)}")
                    
                    # Step 2.4: Update Notion with results
                    if isinstance(result, tuple) and len(result) >= 2:
                        response_text, thought_process = result
                        logger.debug(f"Step 2.4: Updating Notion with results (response length: {len(response_text)})")
                        
                        # First update status and summary
                        await orchestrator.notion_api.update_task_status(
                            page_id=page_id,
                            status="Review",
                            summary=response_text[:2000] if response_text else "No response"
                        )
                        
                        # Then update page content
                        await orchestrator.notion_api.update_page_content(
                            page_id=page_id,
                            content=response_text,
                            thought_process=thought_process
                        )
                        
                        logger.info(f"Successfully processed and updated task {page_id}")
                    else:
                        logger.warning(f"Unexpected result format: {result}")
                        
                except Exception as e:
                    logger.error(f"Error processing task {page_id}: {str(e)}")
                    logger.error(traceback.format_exc())
                    continue
        
        # Process iteration tasks with similar detailed logging
        logger.info("Processing 'Iteration' tasks...")
        # ... similar detailed steps for iteration tasks ...
        
        logger.info("Task processing completed successfully")
        
    except Exception as e:
        logger.error(f"Error in test flow: {str(e)}")
        logger.error(traceback.format_exc())

# Add a simple timeout to prevent hanging indefinitely
async def run_with_timeout():
    try:
        # Set a timeout of 5 minutes (300 seconds) since agent processing can take time
        await asyncio.wait_for(test_flow(), timeout=300)
    except asyncio.TimeoutError:
        logger.error("Test flow timed out after 300 seconds")
    except Exception as e:
        logger.error(f"Unexpected error in run_with_timeout: {str(e)}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    logger.info("Script started")
    try:
        asyncio.run(run_with_timeout())
    except KeyboardInterrupt:
        logger.info("Script interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        logger.error(traceback.format_exc())
    finally:
        logger.info("Script finished")