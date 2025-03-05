"""
Provides a NotionAPI class to interact with the Notion API for reading and updating tasks.
"""

import logging
from typing import Dict, Any, Optional, List
from notion_client import Client
from openai import OpenAI
import traceback
import asyncio

logger = logging.getLogger(__name__)

class NotionAPI:
    """
    A class to handle all Notion API interactions.
    
    Attributes:
        client (Client): The notion-client instance for API communication
        openai_client (OpenAI): The OpenAI instance for LLM integration
        database_id (str): The Notion database ID to query
    """
    
    def __init__(self, notion_api_key: str, openai_api_key: str, database_id: str = "180ee158-0432-8041-b9f0-c28906016b3f"):
        """
        Initialize the NotionAPI with both Notion and OpenAI API keys.
        
        Args:
            notion_api_key (str): The Notion API key for authentication
            openai_api_key (str): The OpenAI API key for LLM integration
            database_id (str): The Notion database ID to query
        """
        self.client = Client(auth=notion_api_key)
        self.openai_client = OpenAI(api_key=openai_api_key)
        self.database_id = database_id
        
    async def get_tasks_to_execute(self) -> List[Dict[str, Any]]:
        """
        Query for all tasks with Status = 'Execute'.
        
        Returns:
            list: List of tasks to be executed
        """
        try:
            response = self.client.databases.query(
                **{
                    "database_id": self.database_id,
                    "filter": {
                        "property": "Status",
                        "status": {
                            "equals": "Execute"
                        }
                    }
                }
            )
            return response.get('results', [])
        except Exception as e:
            logger.error(f"Error querying tasks to execute: {str(e)}")
            return []
    
    async def get_tasks_to_iterate(self) -> List[Dict[str, Any]]:
        """
        Query for all tasks with Status = 'Iterate'.
        
        Returns:
            list: List of tasks to be iterated
        """
        try:
            response = self.client.databases.query(
                **{
                    "database_id": self.database_id,
                    "filter": {
                        "property": "Status",
                        "status": {
                            "equals": "Iterate"
                        }
                    }
                }
            )
            return response.get('results', [])
        except Exception as e:
            logger.error(f"Error querying tasks to iterate: {str(e)}")
            return []
    
    async def get_task(self, page_id: str) -> Dict[str, Any]:
        """
        Retrieve a task from Notion by its page ID.
        
        Args:
            page_id: The Notion page ID
            
        Returns:
            The task details from Notion
        """
        try:
            return self.client.pages.retrieve(page_id=page_id)
        except Exception as e:
            logger.error(f"Error retrieving task {page_id}: {str(e)}")
            raise
    
    async def _run_notion_api(self, func, *args, **kwargs):
        """Run a synchronous Notion API call in a thread pool."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
    
    async def update_task_status(
        self, 
        page_id: str, 
        status: str, 
        summary: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update a task's status and optionally add a summary.
        
        Args:
            page_id: The Notion page ID
            status: The new status value
            summary: Optional summary text to add
            
        Returns:
            The updated page data
        """
        try:
            logger.debug(f"Updating task {page_id} status to '{status}'")
            properties = {
                "Status": {"status": {"name": status}}
            }
            
            if summary:
                logger.debug(f"Adding summary (length: {len(summary)})")
                properties["Response"] = {"rich_text": [{"text": {"content": summary[:2000]}}]}
            
            # Use the helper method to run this in a thread pool
            response = await self._run_notion_api(
                self.client.pages.update,
                page_id=page_id,
                properties=properties
            )
            logger.debug(f"Task status updated successfully for {page_id}")
            return response
        except Exception as e:
            logger.error(f"Error updating task status for {page_id}: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    async def create_error_log(self, page_id: str, error_message: str) -> None:
        """
        Log an error for a task.
        
        Args:
            page_id (str): The Notion page ID
            error_message (str): The error message to log
        """
        try:
            properties = {
                "Status": {"status": {"name": "Error"}},
                "Response": {"rich_text": [{"text": {"content": f"Error: {error_message[:2000]}"}}]}
            }
            
            self.client.pages.update(
                page_id=page_id,
                properties=properties
            )
            
            # Add error callout block
            blocks = [{
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [{"type": "text", "text": {"content": f"Error: {error_message}"}}],
                    "icon": {"emoji": "⚠️"},
                    "color": "red_background"
                }
            }]
            
            await self.update_page_content(page_id, blocks)
            logger.info(f"Error logged to page {page_id}")
        except Exception as e:
            logger.error(f"Error creating error log for {page_id}: {str(e)}")
    
    async def update_page_content(self, page_id: str, content: str, thought_process: str = None) -> None:
        """Update the content of a page with formatted blocks and thought process."""
        try:
            logger.debug(f"Updating page content for {page_id}")
            # First, retrieve existing children to avoid duplicating content
            existing = self.client.blocks.children.list(block_id=page_id)
            
            # Delete existing children if any
            for block in existing.get("results", []):
                logger.debug(f"Deleting existing block {block['id']}")
                self.client.blocks.delete(block_id=block["id"])
            
            # Create new content blocks
            blocks = []
            
            # Add a heading
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "AI Response"}}]
                }
            })
            
            # Split long text into chunks to avoid Notion's 2000 character limit
            content_chunks = self._chunk_text(content)
            logger.debug(f"Split content into {len(content_chunks)} chunks")
            
            # Add the content as paragraph blocks
            for i, chunk in enumerate(content_chunks):
                logger.debug(f"Adding content chunk {i+1}/{len(content_chunks)} (length: {len(chunk)})")
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": chunk}}]
                    }
                })
            
            # Add thought process if available
            if thought_process:
                logger.debug(f"Adding thought process of length {len(thought_process)}")
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
                
                # Split thought process into chunks
                thought_chunks = self._chunk_text(thought_process)
                logger.debug(f"Split thought process into {len(thought_chunks)} chunks")
                
                for i, chunk in enumerate(thought_chunks):
                    logger.debug(f"Adding thought chunk {i+1}/{len(thought_chunks)} (length: {len(chunk)})")
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": chunk}}]
                        }
                    })
            
            # Update the page with new blocks
            logger.debug(f"Sending {len(blocks)} blocks to Notion API")
            response = self.client.blocks.children.append(
                block_id=page_id,
                children=blocks
            )
            logger.debug(f"Successfully updated page content for {page_id}")
            return response
        except Exception as e:
            logger.error(f"Error updating page content for {page_id}: {str(e)}")
            logger.error(traceback.format_exc())
            
            # If the error is related to validation, try a fallback approach
            if "validation_error" in str(e) and thought_process:
                logger.warning("Attempting fallback: Updating without thought process")
                try:
                    # Remove thought process blocks (everything after the divider)
                    divider_index = next((i for i, block in enumerate(blocks) if block.get("type") == "divider"), len(blocks))
                    reduced_blocks = blocks[:divider_index]
                    
                    response = self.client.blocks.children.append(
                        block_id=page_id,
                        children=reduced_blocks
                    )
                    logger.info(f"Fallback successful: Updated page {page_id} without thought process")
                    return response
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {str(fallback_error)}")
            
            # Re-raise the original exception
            raise
    
    def _chunk_text(self, text: str, chunk_size: int = 1900) -> list:
        """
        Split text into chunks to avoid Notion's 2000 character limit.
        
        Args:
            text (str): The text to split into chunks
            chunk_size (int): The maximum size of each chunk (default: 1900)
            
        Returns:
            list: A list of text chunks, each under 2000 characters
        """
        if not text:
            return []
            
        chunks = []
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i + chunk_size]
            # Double-check length to be safe
            if len(chunk) > 2000:
                logger.warning(f"Chunk exceeds 2000 chars ({len(chunk)}), truncating")
                chunk = chunk[:1900] + "..."
            chunks.append(chunk)
        
        return chunks
    
    async def get_page_blocks(self, page_id: str) -> List[Dict[str, Any]]:
        """
        Get all blocks in a page.
        
        Args:
            page_id (str): The Notion page ID
            
        Returns:
            List of block objects
        """
        try:
            response = self.client.blocks.children.list(block_id=page_id)
            return response.get('results', [])
        except Exception as e:
            logger.error(f"Error getting page blocks for {page_id}: {str(e)}")
            return []
    
    async def get_page_comments(self, page_id: str) -> Optional[List[str]]:
        """
        Retrieve both page-level and inline comments from a Notion page.
        
        Args:
            page_id (str): The Notion page ID
            
        Returns:
            List of comment strings or None if no comments found
        """
        comments = []
        
        # Get page-level comments
        try:
            response = self.client.comments.list(block_id=page_id)
            
            for comment in response.get('results', []):
                if 'rich_text' in comment:
                    comment_text = ''.join(
                        text.get('text', {}).get('content', '')
                        for text in comment['rich_text']
                    )
                    if comment_text:
                        comments.append(f"Page comment: {comment_text}")
        except Exception as e:
            logger.error(f"Error getting page comments for {page_id}: {str(e)}")
        
        # Get blocks and their inline comments
        blocks = await self.get_page_blocks(page_id)
        if blocks:
            for block in blocks:
                block_id = block.get('id')
                if block_id:
                    # Get comments for this block
                    try:
                        response = self.client.comments.list(block_id=block_id)
                        
                        for comment in response.get('results', []):
                            if 'rich_text' in comment:
                                comment_text = ''.join(
                                    text.get('text', {}).get('content', '')
                                    for text in comment['rich_text']
                                )
                                if comment_text:
                                    # Include block content for context if available
                                    block_content = block.get(block['type'], {}).get('rich_text', [])
                                    block_text = ''.join(
                                        text.get('text', {}).get('content', '')
                                        for text in block_content
                                    )
                                    if block_text:
                                        comments.append(f"Inline comment on '{block_text}': {comment_text}")
                                    else:
                                        comments.append(f"Inline comment: {comment_text}")
                    except Exception as e:
                        logger.error(f"Error getting comments for block {block_id}: {str(e)}")
                        continue
        
        return comments if comments else None

    async def query_tasks_to_execute(self):
        """Query database for tasks with Status = 'Execute'"""
        logger.debug("Entering query_tasks_to_execute")
        try:
            # Use the helper method to run this in a thread pool
            response = await self._run_notion_api(
                self.client.databases.query,
                **{
                    "database_id": self.database_id,
                    "filter": {
                        "property": "Status",
                        "status": {
                            "equals": "Execute"
                        }
                    }
                }
            )
            logger.debug(f"query_tasks_to_execute found {len(response.get('results', []))} tasks")
            return response
        except Exception as e:
            logger.error(f"Error in query_tasks_to_execute: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {"results": []}

    async def query_tasks_to_iterate(self):
        """Query database for tasks with Status = 'Iterate'"""
        logger.debug("Entering query_tasks_to_iterate")
        try:
            response = self.client.databases.query(
                **{
                    "database_id": self.database_id,
                    "filter": {
                        "property": "Status",
                        "status": {
                            "equals": "Iterate"
                        }
                    }
                }
            )
            logger.debug(f"query_tasks_to_iterate found {len(response.get('results', []))} tasks")
            return response
        except Exception as e:
            logger.error(f"Error in query_tasks_to_iterate: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {"results": []}