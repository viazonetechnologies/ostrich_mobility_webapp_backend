import requests
import json

# Test sales creation with valid data
BASE_URL = "http://localhost:8000"

# Get token
login_data = {"username": "admin", "password": "admin123"}
response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Test valid sale creation with existing customer and product
sale_data = {
    "customer_id": 1,  # From debug test - exists
    "sale_date": "2025-12-30",
    "items": [
        {"product_id": 1, "quantity": 1, "unit_price": 15000.0}  # From debug test - exists
    ]
}

print("Testing sale creation with valid data...")
print(f"Sale data: {sale_data}")
response = requests.post(f"{BASE_URL}/api/v1/sales/", json=sale_data, headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code == 200:
    print("SUCCESS: Sale created!")
else:
    print("FAILED: Sale creation failed")