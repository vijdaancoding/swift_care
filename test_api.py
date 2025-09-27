#!/usr/bin/env python3
"""
Simple test script to verify the Flask API endpoints
"""

import requests
import json

def test_api_endpoints():
    """Test the API endpoints"""
    base_url = "http://127.0.0.1:5000"
    
    print("🧪 Testing Swift Care API Endpoints")
    print("=" * 50)
    
    # Test 1: Get emergencies
    print("\n1. Testing GET /api/v1/emergencies")
    try:
        response = requests.get(f"{base_url}/api/v1/emergencies")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {len(data['data']['emergencies'])} emergencies")
            print(f"   First emergency: {data['data']['emergencies'][0]['title']}")
        else:
            print(f"❌ Failed with status code: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - make sure the Flask app is running")
        return
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Acknowledge emergency
    print("\n2. Testing POST /api/v1/emergencies/1/acknowledge")
    try:
        response = requests.post(f"{base_url}/api/v1/emergencies/1/acknowledge")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! {data['message']}")
        else:
            print(f"❌ Failed with status code: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Test non-existent emergency
    print("\n3. Testing POST /api/v1/emergencies/999/acknowledge (should fail)")
    try:
        response = requests.post(f"{base_url}/api/v1/emergencies/999/acknowledge")
        if response.status_code == 404:
            data = response.json()
            print(f"✅ Expected failure: {data['error']['message']}")
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 API testing complete!")

if __name__ == "__main__":
    test_api_endpoints()
