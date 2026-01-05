#!/usr/bin/env python3
import requests
import json

def test_services_api():
    try:
        # Test the Flask API endpoint
        url = "http://localhost:8000/api/v1/services/"
        headers = {"Authorization": "Bearer test_token"}
        
        print("Testing Flask API endpoint...")
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"API returned {len(data)} service tickets")
            
            # Show first few records
            for i, ticket in enumerate(data[:3]):
                print(f"\n=== TICKET {i+1} ===")
                for key, value in ticket.items():
                    print(f"{key}: {value}")
        else:
            print(f"API Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_services_api()