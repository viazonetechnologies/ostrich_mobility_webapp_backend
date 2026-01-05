#!/usr/bin/env python3
"""
Test script for Sales CRUD operations with validation
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def get_auth_token():
    """Get authentication token"""
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    response = requests.post(f"{API_BASE}/auth/login", json=login_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Login failed: {response.status_code} - {response.text}")
        return None

def test_sales_crud():
    """Test all Sales CRUD operations"""
    print("=== TESTING SALES CRUD OPERATIONS ===\n")
    
    # Get auth token
    token = get_auth_token()
    if not token:
        print("❌ Failed to get auth token")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: Create Sale (should fail with validation)
    print("1. Testing CREATE Sale with missing data...")
    invalid_sale_data = {}
    response = requests.post(f"{API_BASE}/sales/", json=invalid_sale_data, headers=headers)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    assert response.status_code == 400, "Should fail validation"
    print("   ✅ Validation working for missing data\n")
    
    # Test 2: Create Sale with invalid customer
    print("2. Testing CREATE Sale with invalid customer...")
    invalid_customer_sale = {
        "customer_id": 99999,
        "items": [{"product_id": 1, "quantity": 1, "unit_price": 100}]
    }
    response = requests.post(f"{API_BASE}/sales/", json=invalid_customer_sale, headers=headers)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    assert response.status_code == 404, "Should fail with customer not found"
    print("   ✅ Customer validation working\n")
    
    # Test 3: Create Sale with invalid items
    print("3. Testing CREATE Sale with invalid items...")
    invalid_items_sale = {
        "customer_id": 1,
        "items": [{"product_id": 1, "quantity": 0, "unit_price": 100}]
    }
    response = requests.post(f"{API_BASE}/sales/", json=invalid_items_sale, headers=headers)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    assert response.status_code == 400, "Should fail with invalid quantity"
    print("   ✅ Item validation working\n")
    
    # Test 4: Create valid Sale
    print("4. Testing CREATE Sale with valid data...")
    valid_sale_data = {
        "customer_id": 1,
        "sale_date": datetime.now().strftime("%Y-%m-%d"),
        "items": [
            {"product_id": 1, "quantity": 2, "unit_price": 1500.00},
            {"product_id": 2, "quantity": 1, "unit_price": 2500.00}
        ],
        "payment_status": "pending",
        "delivery_status": "pending",
        "notes": "Test sale creation"
    }
    response = requests.post(f"{API_BASE}/sales/", json=valid_sale_data, headers=headers)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    if response.status_code == 201 or response.status_code == 200:
        sale_id = response.json().get("id")
        print(f"   ✅ Sale created successfully with ID: {sale_id}\n")
        
        # Test 5: Read Sale
        print("5. Testing READ Sale...")
        response = requests.get(f"{API_BASE}/sales/{sale_id}", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            sale_data = response.json()
            print(f"   Sale Number: {sale_data.get('sale_number')}")
            print(f"   Customer: {sale_data.get('customer_name')}")
            print(f"   Items: {len(sale_data.get('items', []))}")
            print("   ✅ Sale retrieved successfully\n")
        else:
            print(f"   ❌ Failed to retrieve sale: {response.text}\n")
        
        # Test 6: Update Sale
        print("6. Testing UPDATE Sale...")
        update_data = {
            "payment_status": "paid",
            "delivery_status": "shipped",
            "notes": "Updated test sale"
        }
        response = requests.put(f"{API_BASE}/sales/{sale_id}", json=update_data, headers=headers)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        if response.status_code == 200:
            print("   ✅ Sale updated successfully\n")
        else:
            print(f"   ❌ Failed to update sale\n")
        
        # Test 7: List Sales
        print("7. Testing LIST Sales...")
        response = requests.get(f"{API_BASE}/sales/", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            sales_data = response.json()
            if isinstance(sales_data, dict) and 'sales' in sales_data:
                sales_list = sales_data['sales']
                print(f"   Found {len(sales_list)} sales")
                print(f"   Pagination: {sales_data.get('pagination', {})}")
            else:
                print(f"   Found {len(sales_data)} sales")
            print("   ✅ Sales list retrieved successfully\n")
        else:
            print(f"   ❌ Failed to retrieve sales list: {response.text}\n")
        
        # Test 8: Delete Sale
        print("8. Testing DELETE Sale...")
        response = requests.delete(f"{API_BASE}/sales/{sale_id}", headers=headers)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        if response.status_code == 200:
            print("   ✅ Sale deleted successfully\n")
        else:
            print(f"   ❌ Failed to delete sale\n")
        
        # Test 9: Verify deletion
        print("9. Testing READ deleted Sale...")
        response = requests.get(f"{API_BASE}/sales/{sale_id}", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 404:
            print("   ✅ Sale properly deleted (404 returned)\n")
        else:
            print(f"   ❌ Sale still exists after deletion\n")
    
    else:
        print(f"   ❌ Failed to create sale: {response.text}\n")
    
    print("=== SALES CRUD TESTING COMPLETED ===")

if __name__ == "__main__":
    test_sales_crud()