import asyncio
import logging
import os
import sys
import traceback
from dotenv import load_dotenv
from orchestrator.crew_manager import CrewManager

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def test_crew_manager():
    """Test the CrewManager's ability to process a task"""
    logger.info("Starting CrewManager test...")
    
    # Initialize the CrewManager
    crew_manager = CrewManager()
    
    # Test task
    test_task = "Research the integration of RAG with Notion"
    test_id = "test_id_123"
    
    try:
        # Test crew determination
        logger.info("Testing crew determination...")
        crew_type = await crew_manager.determine_crew(test_task)
        logger.info(f"Crew determination result: {crew_type}")
        
        # Test task processing
        logger.info("Testing task processing...")
        result = await crew_manager.process_task(test_task, test_id)
        
        # Check result
        if isinstance(result, tuple) and len(result) >= 2:
            response, thought_process = result
            logger.info(f"Task processing successful. Response length: {len(response)}")
            logger.info(f"Thought process length: {len(thought_process) if thought_process else 0}")
        else:
            logger.warning(f"Unexpected result format: {result}")
        
        logger.info("CrewManager test completed successfully")
        
    except Exception as e:
        logger.error(f"Error in CrewManager test: {str(e)}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    logger.info("Script started")
    try:
        asyncio.run(test_crew_manager())
    except KeyboardInterrupt:
        logger.info("Script interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        logger.error(traceback.format_exc())
    finally:
        logger.info("Script finished") 