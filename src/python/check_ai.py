import requests

try:
    res = requests.post('http://localhost:5000/api/initialize', json={'dataset': 'iris'})
    data = res.json()
    print(f"AI_ENABLED: {data.get('ai_enabled')}")
except Exception as e:
    print(e)
