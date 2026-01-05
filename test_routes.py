import requests
import json

# Test if backend is running
try:
    response = requests.get("http://localhost:8000/health")
    print(f"Backend health: {response.status_code}")
except:
    print("Backend not running on port 8000")

# Test categories endpoint without auth
try:
    response = requests.get("http://localhost:8000/api/v1/products/categories/")
    print(f"Categories GET (no auth): {response.status_code}")
except Exception as e:
    print(f"Categories GET error: {e}")

# Test with dummy token
headers = {"Authorization": "Bearer dummy_token"}
try:
    response = requests.get("http://localhost:8000/api/v1/products/categories/", headers=headers)
    print(f"Categories GET (with token): {response.status_code}")
except Exception as e:
    print(f"Categories GET with token error: {e}")