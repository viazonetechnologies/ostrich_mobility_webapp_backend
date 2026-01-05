import requests

# Test the simple sale endpoint
try:
    response = requests.post('http://localhost:8001/test-sale', json={})
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")