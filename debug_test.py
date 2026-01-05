import requests
import json

# Test minimal sales creation
BASE_URL = "http://localhost:8000"

# Get token
login_data = {"username": "admin", "password": "admin123"}
response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
if response.status_code != 200:
    print("Login failed:", response.text)
    exit()

token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Test database connection first
print("Testing database connection...")
response = requests.get(f"{BASE_URL}/db-test", headers=headers)
print(f"DB Test Status: {response.status_code}")
print(f"DB Test Response: {response.text}")

# Test customers endpoint
print("\nTesting customers endpoint...")
response = requests.get(f"{BASE_URL}/api/v1/customers/", headers=headers)
print(f"Customers Status: {response.status_code}")
if response.status_code == 200:
    customers = response.json()
    print(f"Found {len(customers)} customers")
    if customers:
        print(f"First customer: {customers[0]}")
else:
    print(f"Customers Error: {response.text}")

# Test products endpoint
print("\nTesting products endpoint...")
response = requests.get(f"{BASE_URL}/api/v1/products/", headers=headers)
print(f"Products Status: {response.status_code}")
if response.status_code == 200:
    products_data = response.json()
    if isinstance(products_data, dict) and 'products' in products_data:
        products = products_data['products']
        print(f"Found {len(products)} products")
        if products:
            print(f"First product: {products[0]}")
    else:
        print(f"Products response: {products_data}")
else:
    print(f"Products Error: {response.text}")