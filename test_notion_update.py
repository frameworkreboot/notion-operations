import asyncio
import logging
import os
from dotenv import load_dotenv
from orchestrator.notion_api import NotionAPI

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def test_notion_update():
    """Test function to update a Notion page"""
    logger.info("Starting Notion update test...")
    
    # Initialize the NotionAPI
    notion_api = NotionAPI(
        notion_api_key=os.getenv("NOTION_API_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Use a test page ID - replace with a real one from your database
    test_page_id = "1adee1580432800c9f4bd5753d76e06d"  # Replace this!
    #https://www.notion.so/test-page-1adee1580432800c9f4bd5753d76e06d?pvs=4
    try:
        # Test updating status
        logger.info("Testing status update...")
        await notion_api.update_task_status(test_page_id, "In progress")
        
        # Test updating content
        logger.info("Testing content update...")
        test_content = "This is a test update from the debugging script."
        await notion_api.update_page_content(test_page_id, test_content)
        
        logger.info("Notion update test completed successfully")
    except Exception as e:
        logger.error(f"Error in Notion update test: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(test_notion_update()) 