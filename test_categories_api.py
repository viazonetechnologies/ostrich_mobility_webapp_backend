import requests
import json

# Test the categories endpoint
try:
    # Get a token first (you might need to adjust this based on your auth system)
    response = requests.get('http://localhost:8000/api/v1/products/categories/')
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Number of categories returned: {len(data)}")
        for cat in data:
            print(f"  ID: {cat.get('id')}, Name: {cat.get('name')}, Active: {cat.get('is_active')}")
    
except Exception as e:
    print(f"Error: {e}")