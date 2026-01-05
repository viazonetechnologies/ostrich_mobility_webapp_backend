import requests
import json

# Test enquiry creation through the API
url = "http://localhost:8000/api/v1/enquiries/"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer test_token"  # This might need a real token
}

data = {
    "customer_id": 1,
    "product_id": 1,
    "quantity": 1,
    "message": "Test enquiry from API test script",
    "status": "new",
    "notes": "Testing enquiry number generation"
}

try:
    print("Testing enquiry creation API...")
    print(f"URL: {url}")
    print(f"Data: {json.dumps(data, indent=2)}")
    
    response = requests.post(url, json=data, headers=headers)
    
    print(f"\nResponse Status: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    
    if response.status_code == 200 or response.status_code == 201:
        result = response.json()
        print(f"Success Response: {json.dumps(result, indent=2)}")
        if 'enquiry_number' in str(result):
            print(f"Enquiry number found in response!")
    else:
        print(f"Error Response: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("Error: Could not connect to server. Make sure the backend is running on port 8000.")
except Exception as e:
    print(f"Error: {e}")