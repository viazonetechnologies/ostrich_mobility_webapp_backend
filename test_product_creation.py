#!/usr/bin/env python3
"""
Test product creation functionality
"""
import requests
import json

def test_product_creation():
    base_url = "http://localhost:8000"
    
    # Test data for creating a product
    product_data = {
        "name": "Test Electric Wheelchair",
        "description": "High-quality electric wheelchair for mobility assistance",
        "category_id": 1,
        "specifications": "Motor: 24V DC, Battery: Lithium-ion, Weight capacity: 120kg",
        "warranty_period": 24,
        "price": 85000.00,
        "is_active": True
    }
    
    try:
        print("Testing product creation...")
        print(f"URL: {base_url}/api/v1/products/")
        print(f"Data: {json.dumps(product_data, indent=2)}")
        
        # Make POST request to create product
        response = requests.post(
            f"{base_url}/api/v1/products/",
            json=product_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"SUCCESS: Product created with ID: {result.get('id')}")
            return result.get('id')
        else:
            print(f"FAILED: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"ERROR: {e}")
        return None

def test_server_connection():
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"Server health check: {response.status_code} - {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Server connection failed: {e}")
        return False

if __name__ == "__main__":
    print("=== TESTING ADD PRODUCT FUNCTIONALITY ===")
    
    # First test server connection
    if test_server_connection():
        print("Server is running, testing product creation...")
        product_id = test_product_creation()
        
        if product_id:
            print(f"Product creation test PASSED - ID: {product_id}")
        else:
            print("Product creation test FAILED")
    else:
        print("Server is not running. Please start the Flask server first.")