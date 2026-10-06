import os
import sys
from dotenv import load_dotenv
from openai import OpenAI

# Load from the root .env
dotenv_path = os.path.join(os.path.dirname(__file__), '../../.env')
print(f"Loading .env from: {os.path.abspath(dotenv_path)}")
loaded = load_dotenv(dotenv_path)
print(f"Loaded .env: {loaded}")

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("ERROR: OPENAI_API_KEY not found in environment.")
    # Try reading file manually just to see if it's there
    try:
        with open(dotenv_path, 'r') as f:
            content = f.read()
            print(f".env content length: {len(content)}")
            if "OPENAI_API_KEY" in content:
                print("OPENAI_API_KEY string is present in file.")
            else:
                print("OPENAI_API_KEY string is MISSING in file.")
    except Exception as e:
        print(f"Could not read .env file: {e}")
    sys.exit(1)

# Mask key for printing
masked_key = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***"
print(f"API Key found: {masked_key}")

if api_key.startswith("sk-your-api-key"):
    print("ERROR: It looks like you haven't replaced the placeholder key.")
    sys.exit(1)

print("\nTesting OpenAI API Connection...")
try:
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Say hello"}],
        max_tokens=5
    )
    print("SUCCESS: OpenAI API is working correctly!")
    print(f"Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"ERROR: API connection failed: {e}")
    sys.exit(1)
