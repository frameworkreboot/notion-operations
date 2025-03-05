import requests

headers = {
    "Authorization": "Bearer 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",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# Define the base URL and webhook endpoint
ngrok_url = "https://0790-178-212-32-246.ngrok-free.app"
webhook_endpoint = "/api/notion-webhook"  # Some services prefer /api/ prefix
full_webhook_url = f"{ngrok_url}{webhook_endpoint}"
# Ensure no trailing slashes
full_webhook_url = full_webhook_url.rstrip('/')

# Your database ID
database_id = "180ee158-0432-8041-b9f0-c28906016b3f"  # Make sure this is correct

# Test URL accessibility first - use the correct endpoint
try:
    print("\nTesting webhook URL accessibility...")
    # Test the health endpoint first
    health_response = requests.get(f"{ngrok_url}/health")
    print(f"Health check status: {health_response.status_code}")
    
    # Then test the webhook endpoint
    webhook_response = requests.get(full_webhook_url)
    print(f"Webhook endpoint check status: {webhook_response.status_code}")
except Exception as e:
    print(f"Error testing URL: {str(e)}")

# Main webhook creation
data = {
    "url": full_webhook_url,
    "events": [
        "page_properties_edited",
        "page_edited",
        "page_created"
    ],
    "filter": {
        "database_id": database_id
    }
}

try:
    print("\nSending request with data:", data)  # Debug print
    response = requests.post(
        "https://api.notion.com/v1/webhooks",
        headers=headers,
        json=data
    )
    
    print(f"Status Code: {response.status_code}")
    print("Response:")
    print(response.json())
    
except Exception as e:
    print(f"Error: {str(e)}")

# Add this to your script to list existing webhooks
try:
    print("\nListing existing webhooks...")
    list_response = requests.get(
        "https://api.notion.com/v1/webhooks",
        headers=headers
    )
    
    print(f"Status Code: {list_response.status_code}")
    print("Response:")
    print(list_response.json())
    
except Exception as e:
    print(f"Error listing webhooks: {str(e)}")