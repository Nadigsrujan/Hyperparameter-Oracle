import requests
import json

base_url = 'http://localhost:5000'

try:
    print("Checking /api/status...")
    response = requests.get(f'{base_url}/api/status')
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    print("\nChecking /api/history...")
    response = requests.get(f'{base_url}/api/history')
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

except Exception as e:
    print(f"Error: {e}")
