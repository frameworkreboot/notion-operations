import pytest
from fastapi.testclient import TestClient
from orchestrator.main import app
from orchestrator.notion_api import NotionAPI
from unittest.mock import Mock, patch

client = TestClient(app)

@pytest.fixture
def mock_notion_api():
    return Mock(spec=NotionAPI)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@patch("orchestrator.webhook_handler.process_notion_webhook")
def test_notion_webhook(mock_process_webhook, mock_notion_api):
    # Test data
    test_payload = {
        "type": "page_created",
        "page": {
            "id": "test-page-id"
        }
    }
    
    mock_process_webhook.return_value = {"status": "success", "task_id": "test-page-id"}
    
    # Make request
    response = client.post("/notion-webhook", json=test_payload)
    
    # Assertions
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    mock_process_webhook.assert_called_once() 