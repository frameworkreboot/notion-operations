"""
Tests the manager agent's logic for routing tasks and synthesizing summaries.
"""
import pytest
from manager_agent.task_router import route_task
from manager_agent.summary_synthesizer import synthesize_summary

@pytest.mark.asyncio
async def test_route_task():
    crew, crew_resp = await route_task("Analyze Sales Data", "Sales data for Q1", None)
    assert crew == "CrewA"
    assert "analysis_result" in crew_resp

def test_synthesize_summary():
    summary = synthesize_summary("CrewB", {"generated_text": "Hello, world!"})
    assert "Text Generation Summary: Hello, world!" in summary
