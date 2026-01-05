import requests
import json

# Test enquiry creation with proper authentication
base_url = "http://localhost:8000"

# Step 1: Login to get a valid token
login_url = f"{base_url}/api/v1/auth/login"
login_data = {
    "username": "admin",
    "password": "admin123"
}

try:
    print("Step 1: Logging in...")
    login_response = requests.post(login_url, json=login_data)
    
    if login_response.status_code == 200:
        login_result = login_response.json()
        token = login_result.get("access_token")
        print(f"Login successful! Token: {token[:20]}...")
        
        # Step 2: Create enquiry with valid token
        enquiry_url = f"{base_url}/api/v1/enquiries/"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        enquiry_data = {
            "customer_id": 1,
            "product_id": 1,
            "quantity": 1,
            "message": "Test enquiry from authenticated API test",
            "status": "new",
            "notes": "Testing enquiry number generation with auth"
        }
        
        print("\nStep 2: Creating enquiry...")
        enquiry_response = requests.post(enquiry_url, json=enquiry_data, headers=headers)
        
        print(f"Enquiry Response Status: {enquiry_response.status_code}")
        
        if enquiry_response.status_code in [200, 201]:
            result = enquiry_response.json()
            print(f"Success! Enquiry created: {json.dumps(result, indent=2)}")
        else:
            print(f"Error creating enquiry: {enquiry_response.text}")
            
        # Step 3: Check what enquiries exist now
        print("\nStep 3: Checking current enquiries...")
        get_response = requests.get(enquiry_url, headers=headers)
        
        if get_response.status_code == 200:
            enquiries = get_response.json()
            print(f"Current enquiries count: {len(enquiries)}")
            if enquiries:
                latest = enquiries[0] if isinstance(enquiries, list) else enquiries
                print(f"Latest enquiry: {json.dumps(latest, indent=2)}")
        
    else:
        print(f"Login failed: {login_response.status_code} - {login_response.text}")
        
except requests.exceptions.ConnectionError:
    print("Error: Could not connect to server. Make sure the backend is running on port 8000.")
except Exception as e:
    print(f"Error: {e}")