import os
from dotenv import load_dotenv
from openai import OpenAI

# Explicitly load .env
load_dotenv('.env')

api_key = os.getenv('OPENAI_API_KEY')
print(f"Loaded API Key: {api_key[:10]}...{api_key[-5:] if api_key else 'None'}")

if not api_key:
    print("ERROR: No API Key found in .env")
    exit(1)

try:
    client = OpenAI(api_key=api_key)
    print("OpenAI client initialized.")
    
    # Simple test call
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hello"}],
        max_tokens=5
    )
    print("API Call Successful!")
    print(f"Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"ERROR: OpenAI connection failed: {e}")
