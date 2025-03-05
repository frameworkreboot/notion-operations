"""
Tests the specialized crew logic, ensuring each crew processes tasks as expected.
"""
import pytest
import os
from dotenv import load_dotenv
from crewai import Crew, Agent, Task

# Load environment variables
load_dotenv()

def test_basic_research_crew():
    """
    Test a basic research crew with a single agent and task.
    Input: A simple research question
    Expected Output: A detailed analysis
    """
    from crews.research_crew.crew import ResearchCrew
    
    # Initialize the crew with test input
    inputs = {
        'topic': 'The impact of AI on software development productivity'
    }
    
    # Execute the crew
    result = ResearchCrew().crew().kickoff(inputs=inputs)
    
    # Basic assertions
    assert result is not None
    assert len(result.raw) > 0  # Use .raw to get the string content
    assert "findings" in result.raw.lower() or "analysis" in result.raw.lower()
    
    print("\nCrew Result:", result.raw)
    return result

if __name__ == "__main__":
    print("Testing Basic Research Crew...")
    test_basic_research_crew()
