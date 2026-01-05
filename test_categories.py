import requests

# Test category endpoints
base_url = "http://localhost:8000"
token = "dummy_token"  # You'll need a real token

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Test GET categories
try:
    response = requests.get(f"{base_url}/api/v1/products/categories/", headers=headers)
    print(f"GET categories: {response.status_code}")
    if response.status_code == 200:
        print(f"Categories: {len(response.json())}")
except Exception as e:
    print(f"GET error: {e}")

# Test PUT category (this is the failing one)
try:
    data = {"name": "Test Category", "description": "Test", "is_active": True}
    response = requests.put(f"{base_url}/api/v1/products/categories/4", headers=headers, json=data)
    print(f"PUT category 4: {response.status_code}")
    if response.status_code != 200:
        print(f"PUT error response: {response.text}")
except Exception as e:
    print(f"PUT error: {e}")

# Test DELETE category
try:
    response = requests.delete(f"{base_url}/api/v1/products/categories/4", headers=headers)
    print(f"DELETE category 4: {response.status_code}")
except Exception as e:
    print(f"DELETE error: {e}")