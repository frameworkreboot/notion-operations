import os
from dotenv import load_dotenv
import requests
import json
from openai import OpenAI
from crewai import Crew, Agent, Task
from crews.research_crew.crew import ResearchCrew

# Load environment variables
load_dotenv()

# Get API keys and IDs
NOTION_API_KEY = os.getenv('NOTION_API_KEY')
NOTION_PAGE_ID = os.getenv('NOTION_PAGE_ID')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
DATABASE_ID = "180ee158-0432-8041-b9f0-c28906016b3f"
SERPER_API_KEY = os.getenv('SERPER_API_KEY')

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Notion API headers
headers = {
    'Authorization': f'Bearer {NOTION_API_KEY}',
    'Content-Type': 'application/json',
    'Notion-Version': '2022-06-28'  # Updated to match the version in the documentation
}

def determine_crew(task_content: str) -> str | None:
    """Use LLM to determine which crew should handle the task"""
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
        print(f"LLM response for crew determination: '{result}'")
        if result == 'research' and not SERPER_API_KEY:
            print("Warning: SERPER_API_KEY not found. Research crew requires this API key.")
            return None
        return 'research' if 'research' in result else None
        
    except Exception as e:
        print(f"Error in crew determination: {str(e)}")
        return None

def get_llm_response(task_content: str) -> tuple[str, str | None]:
    """Get response from OpenAI for a given task"""
    try:
        print(f"\nSending task to OpenAI: {task_content}")
        thought_process = []
        
        def capture_thought(output):
            try:
                if hasattr(output, 'output'):
                    entry = f"Step {len(thought_process) + 1}: {output.output}\n"
                    thought_process.append(entry)
                    print(f"Captured thought: {entry[:100]}...")
                elif hasattr(output, 'result'):
                    entry = f"Tool result: {output.result}\n"
                    thought_process.append(entry)
                    print(f"Captured tool result: {entry[:100]}...")
                elif hasattr(output, 'content'):
                    entry = f"Content: {output.content}\n"
                    thought_process.append(entry)
                    print(f"Captured content: {entry[:100]}...")
                else:
                    entry = f"Tool used: {str(output)}\n"
                    thought_process.append(entry)
                    print(f"Captured tool usage: {entry[:100]}...")
            except Exception as e:
                error_entry = f"Error capturing thought: {str(e)}\n"
                thought_process.append(error_entry)
                print(f"Error in capture_thought: {str(e)}")
        
        crew_type = determine_crew(task_content)
        if crew_type == 'research':
            print("Using Research Crew for this task...")
            try:
                crew = ResearchCrew()
                crew.researcher().step_callback = capture_thought
                crew.senior_researcher().step_callback = capture_thought
                
                # Check if tools are properly initialized
                if not crew.researcher().tools:
                    print("Warning: No tools available for researcher. Using default processing instead.")
                    raise Exception("No tools available")
                    
                result = crew.crew().kickoff(inputs={'topic': task_content})
                if thought_process:
                    joined_thoughts = "\n".join(thought_process)
                    print(f"Total thought process length: {len(joined_thoughts)}")
                    return result.raw, joined_thoughts
                else:
                    print("No thought process captured!")
                    return result.raw, None
            except Exception as e:
                print(f"Error using Research Crew: {str(e)}")
                print("Falling back to default OpenAI processing...")
                # Fall back to default processing
        
        # Fall back to default OpenAI processing
        print("Using default OpenAI processing...")
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
        
    except Exception as e:
        print(f"Error getting response: {str(e)}")
        return f"Error processing task: {str(e)}", None

def query_tasks_to_execute():
    """Query database for tasks with Status = 'Execute'"""
    url = f'https://api.notion.com/v1/databases/{DATABASE_ID}/query'
    
    filter_params = {
        "filter": {
            "property": "Status",
            "status": {
                "equals": "Execute"
            }
        }
    }
    
    try:
        print("\nQuerying for tasks with Status = 'Execute'...")
        response = requests.post(url, headers=headers, json=filter_params)
        
        if response.status_code == 200:
            data = response.json()
            print("\nFound tasks:")
            print(json.dumps(data, indent=4))
            return data
        else:
            print(f'Failed to query tasks. Status code: {response.status_code}')
            print('Response content:', response.text)
            return None
    except Exception as e:
        print(f"Error querying tasks: {str(e)}")
        return None

def update_notion_entry(page_id: str, response_text: str, thought_process: str = None):
    """Update a Notion page with the response and thought process"""
    # First, clear existing content
    blocks_url = f'https://api.notion.com/v1/blocks/{page_id}/children'
    
    # Split long text into chunks
    def chunk_text(text: str, chunk_size: int = 1900) -> list[str]:
        """Split text into chunks with a safety margin below Notion's 2000 char limit"""
        if not text:
            return []
        
        chunks = []
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i + chunk_size]
            # Double-check length to be safe
            if len(chunk) > 2000:
                print(f"Warning: Chunk exceeds 2000 chars ({len(chunk)}), truncating")
                chunk = chunk[:1900] + "..."
            chunks.append(chunk)
        return chunks

    # Create blocks array with proper structure
    blocks = []
    
    # Add AI Response section
    blocks.append({
        "object": "block",
        "type": "heading_2",
        "heading_2": {
            "rich_text": [{"type": "text", "text": {"content": "AI Response"}}]
        }
    })
    
    # Add response content in chunks
    print(f"Response text length: {len(response_text)}")
    response_chunks = chunk_text(response_text)
    print(f"Split into {len(response_chunks)} chunks")
    
    for i, chunk in enumerate(response_chunks):
        print(f"Response chunk {i} length: {len(chunk)}")
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": chunk}}]
            }
        })

    # Add thought process if available
    if thought_process:
        print(f"Thought process length: {len(thought_process)}")
        # Check for unusual characters
        unusual_chars = [char for char in thought_process if ord(char) > 127]
        if unusual_chars:
            print(f"Found {len(unusual_chars)} unusual characters in thought process")
            # Consider replacing or removing them
            for char in set(unusual_chars):
                thought_process = thought_process.replace(char, '')
            print(f"After removing unusual chars, length: {len(thought_process)}")
        blocks.append({
            "object": "block",
            "type": "divider",
            "divider": {}  # Empty object required by Notion API
        })
        
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "Thought Process"}}]
            }
        })
        
        thought_chunks = chunk_text(thought_process)
        print(f"Split thought process into {len(thought_chunks)} chunks")
        
        for i, chunk in enumerate(thought_chunks):
            print(f"Thought chunk {i} length: {len(chunk)}")
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": chunk}}]
                }
            })
    
    print(f"Total blocks to be created: {len(blocks)}")
    
    # Update properties first
    properties_url = f'https://api.notion.com/v1/pages/{page_id}'
    properties_data = {
        "properties": {
            "Status": {"status": {"name": "Review"}},
            "Response": {
                "rich_text": [{"text": {"content": response_text[:2000]}}]
            }
        }
    }

    try:
        # Update properties
        prop_response = requests.patch(properties_url, headers=headers, json=properties_data)
        if prop_response.status_code != 200:
            print(f'Failed to update properties. Status code: {prop_response.status_code}')
            print('Response content:', prop_response.text)
            return False

        # Update content
        content_response = requests.patch(blocks_url, headers=headers, json={"children": blocks})
        if content_response.status_code != 200:
            print(f'Failed to update content. Status code: {content_response.status_code}')
            print('Response content:', content_response.text)
            
            # Fallback: Try again without thought process if that was the issue
            if thought_process and "validation_error" in content_response.text:
                print("Attempting fallback: Updating without thought process")
                # Recreate blocks without thought process
                blocks = blocks[:blocks.index(next(b for b in blocks if b.get("type") == "divider"))]
                fallback_response = requests.patch(blocks_url, headers=headers, json={"children": blocks})
                if fallback_response.status_code == 200:
                    print("Fallback successful: Updated without thought process")
                    return True
            return False

        print("Entry updated successfully!")
        return True

    except Exception as e:
        print(f"Error updating entry: {str(e)}")
        return False

def process_tasks():
    """Main orchestrator function"""
    tasks = query_tasks_to_execute()
    
    if not tasks or 'results' not in tasks:
        print("No tasks found or error occurred")
        return
    
    for task in tasks['results']:
        try:
            task_content = task['properties']['Task']['title'][0]['text']['content']
            print(f"\nProcessing task: {task_content}")
            
            llm_response, thought_process = get_llm_response(task_content)
            success = update_notion_entry(task['id'], llm_response, thought_process)
            
            if success:
                print(f"Successfully processed task: {task_content}")
            else:
                print(f"Failed to process task: {task_content}")
            
        except Exception as e:
            print(f"Error processing task: {str(e)}")
            continue

def query_tasks_to_iterate():
    """Query database for tasks with Status = 'Iterate'"""
    url = f'https://api.notion.com/v1/databases/{DATABASE_ID}/query'
    
    filter_params = {
        "filter": {
            "property": "Status",
            "status": {
                "equals": "Iterate"
            }
        }
    }
    
    try:
        print("\nQuerying for tasks with Status = 'Iterate'...")
        response = requests.post(url, headers=headers, json=filter_params)
        
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f'Failed to query tasks. Status code: {response.status_code}')
            print('Response content:', response.text)
            return None
    except Exception as e:
        print(f"Error querying tasks: {str(e)}")
        return None

def get_page_blocks(page_id: str):
    """Get all blocks in a page"""
    url = f'https://api.notion.com/v1/blocks/{page_id}/children'
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get('results', [])
        else:
            print(f'Failed to get blocks. Status code: {response.status_code}')
            return None
    except Exception as e:
        print(f"Error getting blocks: {str(e)}")
        return None

def get_page_comments(page_id: str):
    """Retrieve both page-level and inline comments from a Notion page"""
    comments = []
    
    # Get page-level comments
    url = f'https://api.notion.com/v1/comments?block_id={page_id}'
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            for comment in data.get('results', []):
                if 'rich_text' in comment:
                    comment_text = ''.join(
                        text.get('text', {}).get('content', '')
                        for text in comment['rich_text']
                    )
                    if comment_text:
                        comments.append(f"Page comment: {comment_text}")
    except Exception as e:
        print(f"Error getting page comments: {str(e)}")
    
    # Get blocks and their inline comments
    blocks = get_page_blocks(page_id)
    if blocks:
        for block in blocks:
            block_id = block.get('id')
            if block_id:
                # Get comments for this block
                url = f'https://api.notion.com/v1/comments?block_id={block_id}'
                try:
                    response = requests.get(url, headers=headers)
                    if response.status_code == 200:
                        data = response.json()
                        for comment in data.get('results', []):
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
                    print(f"Error getting comments for block {block_id}: {str(e)}")
                    continue
    
    return comments if comments else None

def process_iteration_tasks():
    """Process tasks marked for iteration"""
    tasks = query_tasks_to_iterate()
    
    if not tasks or 'results' not in tasks:
        print("No tasks found for iteration")
        return
    
    for task in tasks['results']:
        try:
            task_id = task['id']
            task_title = task['properties']['Task']['title'][0]['text']['content']
            print(f"\nProcessing iteration for task: {task_title}")
            
            # Get comments from the page
            comments = get_page_comments(task_id)
            
            if comments:
                print("\nFound comments:")
                for comment in comments:
                    print(f"- {comment}")
            else:
                print("No comments found for iteration")
                
        except Exception as e:
            print(f"Error processing iteration task: {str(e)}")
            continue

def main():
    """Main function to test all functionality"""
    print("\n=== Starting Notion Task Processor ===")
    
    # Check for required environment variables
    if not all([NOTION_API_KEY, NOTION_PAGE_ID, OPENAI_API_KEY]):
        print("Error: Missing required environment variables!")
        return
    
    process_tasks()  # Process regular tasks
    process_iteration_tasks()  # Process iteration tasks
    print("\n=== Processing Complete ===")

if __name__ == "__main__":
    main()
