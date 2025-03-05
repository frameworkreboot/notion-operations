import asyncio
import logging
from dotenv import load_dotenv
from orchestrator.orchestrator import TaskOrchestrator
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def main_loop():
    """Main loop to run the service continuously"""
    # Initialize the orchestrator
    orchestrator = TaskOrchestrator()
    
    while True:
        try:
            # Process tasks
            await orchestrator.process_execute_tasks()
            await orchestrator.process_iteration_tasks()
            
            # Wait for 5 minutes before checking again
            logger.info("Waiting for 5 minutes before next check...")
            await asyncio.sleep(300)
        except Exception as e:
            logger.error(f"Error in main loop: {str(e)}")
            # Still wait before retrying to avoid rapid failure loops
            await asyncio.sleep(60)

if __name__ == "__main__":
    logger.info("Starting scheduled Notion task processor...")
    asyncio.run(main_loop()) 