import requests
import json

# Test sales creation with minimal data
BASE_URL = "http://localhost:8000"

# Get token
login_data = {"username": "admin", "password": "admin123"}
response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
if response.status_code != 200:
    print("Login failed:", response.text)
    exit()

token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Test valid sale creation
sale_data = {
    "customer_id": 1,
    "sale_date": "2025-12-30",
    "items": [
        {"product_id": 1, "quantity": 1, "unit_price": 100.0}
    ]
}

print("Testing sale creation...")
response = requests.post(f"{BASE_URL}/api/v1/sales/", json=sale_data, headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")