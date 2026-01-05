import requests
import json

# Test which server is handling enquiry requests
base_url = "http://localhost:8000"

# Test 1: Check server type by looking at response headers
try:
    response = requests.get(f"{base_url}/health")
    print(f"Health check response: {response.status_code}")
    print(f"Server header: {response.headers.get('Server', 'Not found')}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Health check failed: {e}")

# Test 2: Try to access a FastAPI-specific endpoint
try:
    response = requests.get(f"{base_url}/docs")
    print(f"\nFastAPI docs response: {response.status_code}")
    if response.status_code == 200:
        print("FastAPI server is running (docs accessible)")
    else:
        print("FastAPI docs not accessible")
except Exception as e:
    print(f"FastAPI docs check failed: {e}")

# Test 3: Check enquiries endpoint without auth to see error format
try:
    response = requests.get(f"{base_url}/api/v1/enquiries/")
    print(f"\nEnquiries endpoint response: {response.status_code}")
    print(f"Response: {response.text}")
    print(f"Content-Type: {response.headers.get('Content-Type', 'Not found')}")
except Exception as e:
    print(f"Enquiries endpoint check failed: {e}")