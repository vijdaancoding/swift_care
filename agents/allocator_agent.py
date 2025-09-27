import os
import requests
import google.generativeai as genai
from typing import Dict, Any, Optional, List


class AllocatorAgent:
    """
    Allocator Agent using the New Google Places API (v1).
    """
    def __init__(self, maps_api_key, api_key):
        if not api_key or not maps_api_key:
            raise ValueError(
                "API keys for Gemini and Google Maps must be set as environment variables."
            )
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        self.llm_model = genai.GenerativeModel('gemini-2.5-flash')
        self.maps_api_key = maps_api_key
        

    def _geocode_location(self, location_text: str) -> Optional[Dict[str, float]]:
        """Geocode location using Google Geocoding API."""
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            'address': f"{location_text}, Pakistan",
            'key': self.maps_api_key
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == 'OK' and data['results']:
                location = data['results'][0]['geometry']['location']
                print(f"Allocator  - Geocoded: {location}")
                return location
            else:
                print(f"Allocator    - Geocoding failed: {data.get('status')}")
                return None
                
        except Exception as e:
            print(f"Allocator    - Geocoding error: {e}")
            return None

    def _search_places_nearby(self, query: str, location: Dict[str, float], location_text: str, max_results: int = 5) -> List[Dict]:
        """
        Search for places using the New Places API with location bias.
        """
        url = "https://places.googleapis.com/v1/places:searchText"
        headers = {
            'Content-Type': 'application/json',
            'X-Goog-Api-Key': self.maps_api_key,
            'X-Goog-FieldMask': 'places.displayName,places.formattedAddress,places.location,places.rating,places.userRatingCount'
        }
        
        # Create location bias for better nearby results
        location_bias = {
            "circle": {
                "center": {
                    "latitude": location['lat'],
                    "longitude": location['lng']
                },
                "radius": 10000.0  # 10km radius
            }
        }
        
        # Use the actual location in the query instead of hardcoded "Karachi"
        payload = {
            "textQuery": f"{query} near {location_text}, Pakistan",
            "maxResultCount": max_results,
            "locationBias": location_bias
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            if 'places' in data:
                return data['places']
            else:
                print(f"Allocator    - No places found in response")
                return []
                
        except Exception as e:
            print(f"Allocator    - Places search error: {e}")
            return []

    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate approximate distance between two points (in km)."""
        # Simple Euclidean distance approximation for nearby locations
        lat_diff = lat1 - lat2
        lng_diff = lng1 - lng2
        return ((lat_diff ** 2 + lng_diff ** 2) ** 0.5) * 111.32  # Rough km conversion

    def _find_nearest_facility(self, service_keyword: str, location_text: str) -> Optional[Dict[str, Any]]:
        """
        Find nearest facility using New Places API with location-based sorting.
        """
        print(f"Allocator -  Autonomous Tool Use: Engaging New Places API.")
        
        # Step 1: Get coordinates
        print(f"Allocator   - Step 1: Geocoding '{location_text}'...")
        coordinates = self._geocode_location(location_text)
        if not coordinates:
            return None

        # Step 2: Search for places
        print(f"Allocator    - Step 2: Searching for '{service_keyword}'...")
        places = self._search_places_nearby(service_keyword, coordinates, location_text)
        
        if not places:
            return None

        # Step 3: Find closest facility
        target_lat, target_lng = coordinates['lat'], coordinates['lng']
        closest_place = None
        min_distance = float('inf')
        
        for place in places:
            if 'location' in place:
                place_lat = place['location']['latitude']
                place_lng = place['location']['longitude']
                distance = self._calculate_distance(target_lat, target_lng, place_lat, place_lng)
                
                if distance < min_distance:
                    min_distance = distance
                    closest_place = place

        if closest_place:
            facility_info = {
                "name": closest_place['displayName']['text'],
                "address": closest_place.get('formattedAddress', 'Address not available'),
                "distance_km": round(min_distance, 2),
                "rating": closest_place.get('rating', 'N/A'),
                "total_ratings": closest_place.get('userRatingCount', 0)
            }
            print(f"Allocator     - Found: {facility_info['name']} ({facility_info['distance_km']} km)")
            return facility_info
        
        return None

    def _generate_llm_recommendation(
        self, incident_type: str, summary: str, location: str, facility_info: Optional[Dict]
    ) -> str:
        """Generate contextual recommendation using Gemini LLM."""
        print(f"Allocator -  Autonomous Tool Use: Engaging Gemini LLM.")
        
        if facility_info:
            facility_context = f"""
- *Identified Facility:* {facility_info['name']}
- *Address:* {facility_info['address']}
- *Distance:* {facility_info['distance_km']} km from incident
- *Rating:* {facility_info.get('rating', 'N/A')} ({facility_info.get('total_ratings', 0)} reviews)
"""
        else:
            facility_context = "- *Facility Status:* No specific facility identified. Use standard emergency protocols."

        prompt = f"""
You are an emergency dispatcher for Pakistan. Generate a precise call-to-action.

*INCIDENT REPORT:*
- *Type:* {incident_type}
- *Location:* {location}
- *Details:* {summary}

*RESOURCE ALLOCATION:*
{facility_context}

*TASK:* Create a concise emergency dispatch instruction (max 40 words) that includes:
1. Priority level (HIGH/MEDIUM/LOW)
2. Units to dispatch 
3. Destination
4. Brief tactical note

*FORMAT:* Direct command style, no extra formatting.
"""
        
        try:
            response = self.llm_model.generate_content(prompt)
            recommendation = response.text.strip().replace('*', '').replace('', '')
            print(f"Allocator    - Generated recommendation")
            return recommendation
        except Exception as e:
            print(f"Allocator    - LLM error: {e}")
            fallback = f"HIGH PRIORITY: Dispatch emergency units to {incident_type.lower()} at {location}."
            if facility_info:
                fallback += f" Route to {facility_info['name']}."
            return fallback

    def process_incident(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main incident processing with optimized workflow."""
        incident_type = incident_data.get("incident_type")
        summary = incident_data.get("summary")  
        location = incident_data.get("location")

        print(f"\nAllocator - Processing {incident_type} incident at '{location}'")

        # Enhanced service mapping for Pakistan context
        service_mapping = {
            "Medical": "hospital emergency medical center",
            "Crime": "police station",
            "Disaster": "emergency services rescue"
        }
        
        service_keyword = service_mapping.get(incident_type)
        if not service_keyword:
            raise ValueError(f"Unsupported incident type: {incident_type}")

        # Find nearest appropriate facility
        facility_info = self._find_nearest_facility(service_keyword, location)
        
        # Generate AI recommendation
        call_to_action = self._generate_llm_recommendation(
            incident_type, summary, location, facility_info
        )

        # Compile results
        result = {
            "incident_type": incident_type,
            "location_reported": location,
            "facility_found": facility_info is not None,
            "nearest_facility": facility_info or {"status": "none_found"},
            "ai_recommendation": call_to_action,
            "processing_status": "completed"
        }
        
        return result