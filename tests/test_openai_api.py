import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Get API key
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("Missing OPENAI_API_KEY in .env file")

# Initialize OpenAI client
client = OpenAI(api_key=api_key)  # No need for base_url with personal OpenAI key

# Test API call
try:
    print("\nTesting OpenAI API connection...")
    print(f"Using API key starting with: {api_key[:8]}...")
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"}
        ]
    )

    # Debug print entire response
    print("\nRaw API Response:", response)

    # Print only the message
    print("\nAssistant:", response.choices[0].message.content)

except Exception as e:
    print(f"Error calling OpenAI API: {str(e)}")
    print(f"Full error details: {repr(e)}")
