import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

def test_geocoding_api():
    """Test if Geocoding API is working correctly."""
    print("=== TESTING GEOCODING API ===")
    
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        'address': 'Shahrah-e-Faisal, Karachi, Pakistan',
        'key': GOOGLE_MAPS_API_KEY
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"API Status: {data.get('status')}")
        
        if data['status'] == 'OK':
            location = data['results'][0]['geometry']['location']
            print(f"✅ Geocoding Success: {location}")
            return location
        else:
            print(f"❌ Geocoding Failed: {data}")
            return None
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

def test_places_text_search():
    """Test Places API Text Search endpoint."""
    print("\n=== TESTING PLACES API (TEXT SEARCH) ===")
    
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        'query': 'hospital in Karachi, Pakistan',
        'key': GOOGLE_MAPS_API_KEY
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"API Status: {data.get('status')}")
        print(f"Error Message: {data.get('error_message', 'None')}")
        
        if data['status'] == 'OK':
            print(f"✅ Found {len(data['results'])} places")
            if data['results']:
                first_result = data['results'][0]
                print(f"First result: {first_result['name']}")
                print(f"Address: {first_result.get('formatted_address', 'N/A')}")
        else:
            print(f"❌ Places API Failed")
            print(f"Full response: {json.dumps(data, indent=2)}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_places_nearby_search():
    """Test Places API Nearby Search endpoint."""
    print("\n=== TESTING PLACES API (NEARBY SEARCH) ===")
    
    # First get coordinates from geocoding
    location = test_geocoding_api()
    if not location:
        print("Cannot test nearby search without coordinates")
        return
    
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        'location': f"{location['lat']},{location['lng']}",
        'radius': 5000,  # 5km radius
        'type': 'hospital',
        'key': GOOGLE_MAPS_API_KEY
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"API Status: {data.get('status')}")
        print(f"Error Message: {data.get('error_message', 'None')}")
        
        if data['status'] == 'OK':
            print(f"✅ Found {len(data['results'])} nearby places")
            if data['results']:
                first_result = data['results'][0]
                print(f"Closest: {first_result['name']}")
                print(f"Address: {first_result.get('vicinity', 'N/A')}")
        else:
            print(f"❌ Nearby Search Failed")
            print(f"Full response: {json.dumps(data, indent=2)}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_places_new_api():
    """Test the new Places API (Places API New) endpoint."""
    print("\n=== TESTING NEW PLACES API ===")
    
    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': GOOGLE_MAPS_API_KEY,
        'X-Goog-FieldMask': 'places.displayName,places.formattedAddress,places.location'
    }
    
    data = {
        "textQuery": "hospital in Karachi, Pakistan",
        "maxResultCount": 5
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        result = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200 and 'places' in result:
            print(f"✅ New Places API Success: Found {len(result['places'])} places")
            for place in result['places'][:2]:  # Show first 2 results
                print(f"  - {place.get('displayName', {}).get('text', 'Unknown')}")
                print(f"    Address: {place.get('formattedAddress', 'N/A')}")
        else:
            print(f"❌ New Places API Failed")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    print("🔍 GOOGLE MAPS API DIAGNOSTIC TEST")
    print(f"API Key (first 10 chars): {GOOGLE_MAPS_API_KEY[:10]}..." if GOOGLE_MAPS_API_KEY else "❌ No API Key")
    print("=" * 50)
    
    if not GOOGLE_MAPS_API_KEY:
        print("❌ GOOGLE_MAPS_API_KEY not found in environment variables")
        exit(1)
    
    # Test all endpoints
    test_geocoding_api()
    test_places_text_search() 
    test_places_nearby_search()
    test_places_new_api()
    
    print("\n" + "=" * 50)
    print("🏁 DIAGNOSTIC COMPLETE") 