"""
Provides functionality to synthesize final summaries from crew outputs.
Handles different response formats from various crew types.
"""

from typing import Any, Dict, Optional

def synthesize_summary(crew_identifier: str, crew_response: Dict[str, Any]) -> str:
    """
    Creates a human-readable summary from the crew response.
    
    Args:
        crew_identifier (str): Identifier for the crew that processed the task
                             (e.g., "analysis_crew", "content_crew", "dev_crew")
        crew_response (Dict[str, Any]): The response data returned by the crew
    
    Returns:
        str: Formatted summary suitable for Notion
    
    Example:
        >>> result = synthesize_summary("analysis_crew", 
        ...     {"analysis": "Found 3 key trends", "confidence": 0.95})
        >>> print(result)
        "Analysis Results (95% confidence): Found 3 key trends"
    """
    # Handle error responses
    if "error" in crew_response:
        return f"Error during processing: {crew_response['error']}"
    
    # Process based on crew type
    if crew_identifier == "analysis_crew":
        return _format_analysis_summary(crew_response)
    elif crew_identifier == "content_crew":
        return _format_content_summary(crew_response)
    elif crew_identifier == "dev_crew":
        return _format_dev_summary(crew_response)
    else:
        return f"Unhandled crew type: {crew_identifier}"

def _format_analysis_summary(response: Dict[str, Any]) -> str:
    """
    Formats analysis crew responses.
    
    Args:
        response (Dict[str, Any]): Analysis crew output
        
    Returns:
        str: Formatted analysis summary
    """
    analysis = response.get("analysis", "No analysis provided")
    confidence = response.get("confidence", None)
    
    if confidence is not None:
        return f"Analysis Results ({int(confidence * 100)}% confidence): {analysis}"
    return f"Analysis Results: {analysis}"

def _format_content_summary(response: Dict[str, Any]) -> str:
    """
    Formats content crew responses.
    
    Args:
        response (Dict[str, Any]): Content crew output
        
    Returns:
        str: Formatted content summary
    """
    content_type = response.get("type", "content")
    word_count = response.get("word_count", 0)
    summary = response.get("summary", "No content generated")
    
    return f"{content_type.title()} Created ({word_count} words): {summary}"

def _format_dev_summary(response: Dict[str, Any]) -> str:
    """
    Formats development crew responses.
    
    Args:
        response (Dict[str, Any]): Development crew output
        
    Returns:
        str: Formatted development summary
    """
    action = response.get("action", "code review")
    files_affected = response.get("files_affected", [])
    summary = response.get("summary", "No development work summarized")
    
    files_str = f" ({len(files_affected)} files affected)" if files_affected else ""
    return f"Development {action.title()}{files_str}: {summary}"
