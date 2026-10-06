import requests
import json
import time

base_url = 'http://localhost:5000'

def run_test():
    print("1. Checking Status (Before Init)...")
    try:
        res = requests.get(f'{base_url}/api/status')
        print(f"   Status: {res.status_code}, Initialized: {res.json().get('initialized')}")
    except Exception as e:
        print(f"   Failed to connect: {e}")
        return

    print("\n2. Initializing Oracle (Dataset: iris)...")
    try:
        res = requests.post(f'{base_url}/api/initialize', json={'dataset': 'iris'})
        data = res.json()
        print(f"   Status: {res.status_code}")
        print(f"   Message: {data.get('message')}")
        print(f"   AI Enabled: {data.get('ai_enabled')}")
        
        if res.status_code != 200:
            print("   Initialization Failed! Exiting.")
            return
            
    except Exception as e:
        print(f"   Failed to initialize: {e}")
        return

    print("\n3. Starting Optimization...")
    try:
        res = requests.post(f'{base_url}/api/start', json={'iterations': 5})
        print(f"   Status: {res.status_code}, Message: {res.json().get('message')}")
    except Exception as e:
        print(f"   Failed to start: {e}")
        return

    print("\n4. Waiting for 3 seconds...")
    time.sleep(3)

    print("\n5. Checking History...")
    try:
        res = requests.get(f'{base_url}/api/history')
        history = res.json().get('history', [])
        print(f"   History Items: {len(history)}")
        if len(history) > 0:
            print(f"   Latest Item: {json.dumps(history[-1], indent=2)}")
        else:
            print("   No history items found.")
            
    except Exception as e:
        print(f"   Failed to get history: {e}")

    print("\n6. Stopping Optimization...")
    try:
        requests.post(f'{base_url}/api/stop')
        print("   Stopped.")
    except:
        pass

if __name__ == "__main__":
    run_test()
