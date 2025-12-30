#!/usr/bin/env python3
"""
Comprehensive API Test Script for Ostrich Backend
Tests all CRUD operations for sales, services, enquiries, and users endpoints
"""

import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000"
API_V1_URL = f"{BASE_URL}/api/v1"

def get_auth_token():
    """Get authentication token"""
    response = requests.post(f"{API_V1_URL}/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def test_endpoint(method, url, headers=None, json_data=None):
    """Test an endpoint and return response"""
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=json_data)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=json_data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        
        return {
            "status_code": response.status_code,
            "data": response.json() if response.content else {},
            "success": response.status_code < 400
        }
    except Exception as e:
        return {
            "status_code": 0,
            "data": {"error": str(e)},
            "success": False
        }

def run_tests():
    """Run comprehensive API tests"""
    print("🚀 Starting Ostrich API Tests")
    print("=" * 50)
    
    # Get auth token
    token = get_auth_token()
    if not token:
        print("❌ Failed to get auth token")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test results
    results = {
        "sales": {"list": False, "create": False, "get": False, "update": False, "delete": False},
        "services": {"list": False, "create": False, "get": False, "update": False, "delete": False},
        "enquiries": {"list": False, "create": False, "get": False, "update": False, "delete": False},
        "users": {"list": False, "create": False, "get": False, "update": False, "delete": False}
    }
    
    # Test Sales endpoints
    print("\n📊 Testing Sales Endpoints")
    print("-" * 30)
    
    # Sales - List (both API v1 and fallback)
    for url in [f"{API_V1_URL}/sales/", f"{BASE_URL}/sales/"]:
        result = test_endpoint("GET", url, headers)
        if result["success"]:
            results["sales"]["list"] = True
            print(f"✅ GET {url} - {result['status_code']}")
            break
        else:
            print(f"❌ GET {url} - {result['status_code']}")
    
    # Sales - Create
    sale_data = {
        "customer_id": 1,
        "sale_date": "2025-12-30",
        "total_amount": 25000.0,
        "final_amount": 23750.0,
        "payment_status": "pending",
        "delivery_status": "pending"
    }
    
    for url in [f"{API_V1_URL}/sales/", f"{BASE_URL}/sales/"]:
        result = test_endpoint("POST", url, headers, sale_data)
        if result["success"]:
            results["sales"]["create"] = True
            sale_id = result["data"].get("id", 1)
            print(f"✅ POST {url} - {result['status_code']} (ID: {sale_id})")
            break
        else:
            print(f"❌ POST {url} - {result['status_code']}")
            sale_id = 1
    
    # Sales - Get individual
    for url in [f"{API_V1_URL}/sales/{sale_id}", f"{BASE_URL}/sales/{sale_id}"]:
        result = test_endpoint("GET", url, headers)
        if result["success"]:
            results["sales"]["get"] = True
            print(f"✅ GET {url} - {result['status_code']}")
            break
        else:
            print(f"❌ GET {url} - {result['status_code']}")
    
    # Sales - Update
    update_data = {"payment_status": "paid", "delivery_status": "delivered"}
    for url in [f"{API_V1_URL}/sales/{sale_id}", f"{BASE_URL}/sales/{sale_id}"]:
        result = test_endpoint("PUT", url, headers, update_data)
        if result["success"]:
            results["sales"]["update"] = True
            print(f"✅ PUT {url} - {result['status_code']}")
            break
        else:
            print(f"❌ PUT {url} - {result['status_code']}")
    
    # Sales - Delete
    for url in [f"{API_V1_URL}/sales/{sale_id}", f"{BASE_URL}/sales/{sale_id}"]:
        result = test_endpoint("DELETE", url, headers)
        if result["success"]:
            results["sales"]["delete"] = True
            print(f"✅ DELETE {url} - {result['status_code']}")
            break
        else:
            print(f"❌ DELETE {url} - {result['status_code']}")
    
    # Test Services endpoints
    print("\n🔧 Testing Services Endpoints")
    print("-" * 30)
    
    # Services - List
    for url in [f"{API_V1_URL}/services/", f"{BASE_URL}/services/"]:
        result = test_endpoint("GET", url, headers)
        if result["success"]:
            results["services"]["list"] = True
            print(f"✅ GET {url} - {result['status_code']}")
            break
        else:
            print(f"❌ GET {url} - {result['status_code']}")
    
    # Services - Create
    service_data = {
        "customer_id": 1,
        "product_serial_number": "OST-TEST-001",
        "issue_description": "Test service ticket",
        "priority": "MEDIUM",
        "status": "OPEN"
    }
    
    result = test_endpoint("POST", f"{API_V1_URL}/services/", headers, service_data)
    if result["success"]:
        results["services"]["create"] = True
        service_id = result["data"].get("id", 1)
        print(f"✅ POST {API_V1_URL}/services/ - {result['status_code']} (ID: {service_id})")
    else:
        print(f"❌ POST {API_V1_URL}/services/ - {result['status_code']}")
        service_id = 1
    
    # Services - Get individual
    for url in [f"{API_V1_URL}/services/{service_id}", f"{BASE_URL}/services/{service_id}"]:
        result = test_endpoint("GET", url, headers)
        if result["success"]:
            results["services"]["get"] = True
            print(f"✅ GET {url} - {result['status_code']}")
            break
        else:
            print(f"❌ GET {url} - {result['status_code']}")
    
    # Services - Update
    update_data = {"status": "IN_PROGRESS", "priority": "HIGH"}
    for url in [f"{API_V1_URL}/services/{service_id}", f"{BASE_URL}/services/{service_id}"]:
        result = test_endpoint("PUT", url, headers, update_data)
        if result["success"]:
            results["services"]["update"] = True
            print(f"✅ PUT {url} - {result['status_code']}")
            break
        else:
            print(f"❌ PUT {url} - {result['status_code']}")
    
    # Services - Delete
    for url in [f"{API_V1_URL}/services/{service_id}", f"{BASE_URL}/services/{service_id}"]:
        result = test_endpoint("DELETE", url, headers)
        if result["success"]:
            results["services"]["delete"] = True
            print(f"✅ DELETE {url} - {result['status_code']}")
            break
        else:
            print(f"❌ DELETE {url} - {result['status_code']}")
    
    # Test Enquiries endpoints
    print("\n❓ Testing Enquiries Endpoints")
    print("-" * 30)
    
    # Enquiries - List
    for url in [f"{API_V1_URL}/enquiries/", f"{BASE_URL}/enquiries/"]:
        result = test_endpoint("GET", url, headers)
        if result["success"]:
            results["enquiries"]["list"] = True
            print(f"✅ GET {url} - {result['status_code']}")
            break
        else:
            print(f"❌ GET {url} - {result['status_code']}")
    
    # Enquiries - Create
    enquiry_data = {
        "customer_id": 1,
        "product_id": 1,
        "quantity": 2,
        "message": "Test enquiry for product pricing",
        "status": "open"
    }
    
    result = test_endpoint("POST", f"{API_V1_URL}/enquiries/", headers, enquiry_data)
    if result["success"]:
        results["enquiries"]["create"] = True
        enquiry_id = result["data"].get("id", 1)
        print(f"✅ POST {API_V1_URL}/enquiries/ - {result['status_code']} (ID: {enquiry_id})")
    else:
        print(f"❌ POST {API_V1_URL}/enquiries/ - {result['status_code']}")
        enquiry_id = 1
    
    # Enquiries - Get individual
    for url in [f"{API_V1_URL}/enquiries/{enquiry_id}", f"{BASE_URL}/enquiries/{enquiry_id}"]:
        result = test_endpoint("GET", url, headers)
        if result["success"]:
            results["enquiries"]["get"] = True
            print(f"✅ GET {url} - {result['status_code']}")
            break
        else:
            print(f"❌ GET {url} - {result['status_code']}")
    
    # Enquiries - Update
    update_data = {"status": "in_progress", "notes": "Following up with customer"}
    for url in [f"{API_V1_URL}/enquiries/{enquiry_id}", f"{BASE_URL}/enquiries/{enquiry_id}"]:
        result = test_endpoint("PUT", url, headers, update_data)
        if result["success"]:
            results["enquiries"]["update"] = True
            print(f"✅ PUT {url} - {result['status_code']}")
            break
        else:
            print(f"❌ PUT {url} - {result['status_code']}")
    
    # Enquiries - Delete
    for url in [f"{API_V1_URL}/enquiries/{enquiry_id}", f"{BASE_URL}/enquiries/{enquiry_id}"]:
        result = test_endpoint("DELETE", url, headers)
        if result["success"]:
            results["enquiries"]["delete"] = True
            print(f"✅ DELETE {url} - {result['status_code']}")
            break
        else:
            print(f"❌ DELETE {url} - {result['status_code']}")
    
    # Test Users endpoints
    print("\n👥 Testing Users Endpoints")
    print("-" * 30)
    
    # Users - List
    for url in [f"{API_V1_URL}/users/", f"{BASE_URL}/users/"]:
        result = test_endpoint("GET", url, headers)
        if result["success"]:
            results["users"]["list"] = True
            print(f"✅ GET {url} - {result['status_code']}")
            break
        else:
            print(f"❌ GET {url} - {result['status_code']}")
    
    # Users - Create
    user_data = {
        "username": "testuser",
        "email": "test@ostrich.com",
        "first_name": "Test",
        "last_name": "User",
        "role": "user",
        "phone": "9876543210"
    }
    
    result = test_endpoint("POST", f"{API_V1_URL}/users/", headers, user_data)
    if result["success"]:
        results["users"]["create"] = True
        user_id = result["data"].get("id", 1)
        print(f"✅ POST {API_V1_URL}/users/ - {result['status_code']} (ID: {user_id})")
    else:
        print(f"❌ POST {API_V1_URL}/users/ - {result['status_code']}")
        user_id = 1
    
    # Users - Get individual
    for url in [f"{API_V1_URL}/users/{user_id}", f"{BASE_URL}/users/{user_id}"]:
        result = test_endpoint("GET", url, headers)
        if result["success"]:
            results["users"]["get"] = True
            print(f"✅ GET {url} - {result['status_code']}")
            break
        else:
            print(f"❌ GET {url} - {result['status_code']}")
    
    # Users - Update
    update_data = {"role": "manager", "is_active": True}
    for url in [f"{API_V1_URL}/users/{user_id}", f"{BASE_URL}/users/{user_id}"]:
        result = test_endpoint("PUT", url, headers, update_data)
        if result["success"]:
            results["users"]["update"] = True
            print(f"✅ PUT {url} - {result['status_code']}")
            break
        else:
            print(f"❌ PUT {url} - {result['status_code']}")
    
    # Users - Delete
    for url in [f"{API_V1_URL}/users/{user_id}", f"{BASE_URL}/users/{user_id}"]:
        result = test_endpoint("DELETE", url, headers)
        if result["success"]:
            results["users"]["delete"] = True
            print(f"✅ DELETE {url} - {result['status_code']}")
            break
        else:
            print(f"❌ DELETE {url} - {result['status_code']}")
    
    # Test additional list endpoints
    print("\n📋 Testing Additional List Endpoints")
    print("-" * 30)
    
    additional_endpoints = [
        "/api/v1/customers/",
        "/api/v1/products/",
        "/api/v1/dispatch/",
        "/api/v1/notifications/",
        "/api/v1/regions/"
    ]
    
    for endpoint in additional_endpoints:
        result = test_endpoint("GET", f"{BASE_URL}{endpoint}", headers)
        status = "✅" if result["success"] else "❌"
        print(f"{status} GET {endpoint} - {result['status_code']}")
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    total_tests = 0
    passed_tests = 0
    
    for entity, operations in results.items():
        print(f"\n{entity.upper()}:")
        for operation, success in operations.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"  {operation.upper()}: {status}")
            total_tests += 1
            if success:
                passed_tests += 1
    
    print(f"\nOVERALL: {passed_tests}/{total_tests} tests passed ({(passed_tests/total_tests)*100:.1f}%)")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Check the logs above.")

if __name__ == "__main__":
    run_tests()