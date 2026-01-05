import requests

# Test customer products endpoint
BASE_URL = "http://localhost:8000"

# Get token
login_data = {"username": "admin", "password": "admin123"}
response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
if response.status_code != 200:
    print("Login failed:", response.text)
    exit()

token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Test both routes
print("Testing /api/v1/customers/1/products...")
response = requests.get(f"{BASE_URL}/api/v1/customers/1/products", headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")

print("\nTesting /api/v1/products/by-customer/1...")
response = requests.get(f"{BASE_URL}/api/v1/products/by-customer/1", headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")