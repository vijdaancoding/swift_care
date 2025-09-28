import os
import requests
import google.generativeai as genai
from typing import Dict, Any, Optional, List
import uuid
from datetime import datetime, timezone
import re
import random

class AllocatorAgent:
    """
    Allocator Agent using the New Google Places API (v1) and generating UI-compliant output.
    """
    def __init__(self, maps_api_key, api_key):
        if not api_key or not maps_api_key:
            raise ValueError(
                "API keys for Gemini and Google Maps must be set as environment variables."
            )
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        self.llm_model = genai.GenerativeModel('gemini-2.0-flash')
        self.maps_api_key = maps_api_key
        
        # Predefined dummy data for reporters
        self.dummy_reporters = [
            {"id": 101, "name": "Aisha Khan", "phone": "+923001234567"},
            {"id": 102, "name": "Bilal Ahmed", "phone": "+923338765432"},
            {"id": 103, "name": "Fatima Ali", "phone": "+923215556789"},
            {"id": 104, "name": "Zain Shah", "phone": "+923459876543"}
        ]

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
        """Search for places using the New Places API with location bias."""
        url = "https://places.googleapis.com/v1/places:searchText"
        headers = {
            'Content-Type': 'application/json',
            'X-Goog-Api-Key': self.maps_api_key,
            'X-Goog-FieldMask': 'places.displayName,places.formattedAddress,places.location,places.rating,places.userRatingCount'
        }
        location_bias = {
            "circle": {"center": {"latitude": location['lat'], "longitude": location['lng']}, "radius": 10000.0}
        }
        payload = {"textQuery": f"{query} near {location_text}, Pakistan", "maxResultCount": max_results, "locationBias": location_bias}
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get('places', [])
        except Exception as e:
            print(f"Allocator    - Places search error: {e}")
            return []

    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate approximate distance between two points (in km)."""
        return ((lat1 - lat2) ** 2 + (lng1 - lng2) ** 2) ** 0.5 * 111.32

    def _find_nearest_facility(self, service_keyword: str, location_text: str) -> Optional[Dict[str, Any]]:
        """Find nearest facility using New Places API with location-based sorting."""
        print(f"Allocator -  Autonomous Tool Use: Engaging New Places API.")
        coordinates = self._geocode_location(location_text)
        if not coordinates:
            return None

        places = self._search_places_nearby(service_keyword, coordinates, location_text)
        if not places:
            return None

        target_lat, target_lng = coordinates['lat'], coordinates['lng']
        closest_place = min(
            (place for place in places if 'location' in place),
            key=lambda p: self._calculate_distance(target_lat, target_lng, p['location']['latitude'], p['location']['longitude']),
            default=None
        )

        if closest_place:
            distance = self._calculate_distance(target_lat, target_lng, closest_place['location']['latitude'], closest_place['location']['longitude'])
            facility_info = {
                "name": closest_place['displayName']['text'],
                "address": closest_place.get('formattedAddress', 'Address not available'),
                "distance_km": round(distance, 2),
                "rating": closest_place.get('rating', 'N/A'),
                "total_ratings": closest_place.get('userRatingCount', 0),
                "location": closest_place.get('location')
            }
            print(f"Allocator     - Found: {facility_info['name']} ({facility_info['distance_km']} km)")
            return facility_info
        return None

    def _generate_llm_recommendation(self, incident_type: str, summary: str, location: str, facility_info: Optional[Dict]) -> str:
        """Generate contextual recommendation using Gemini LLM."""
        print(f"Allocator -  Autonomous Tool Use: Engaging Gemini LLM.")
        facility_context = "- *Facility Status:* No specific facility identified. Use standard emergency protocols."
        if facility_info:
            facility_context = f"""
- *Identified Facility:* {facility_info['name']}
- *Address:* {facility_info['address']}
- *Distance:* {facility_info['distance_km']} km from incident
- *Rating:* {facility_info.get('rating', 'N/A')} ({facility_info.get('total_ratings', 0)} reviews)
"""
        prompt = f"""
You are an emergency dispatcher for Pakistan. Generate a precise call-to-action.

*INCIDENT REPORT:*
- *Type:* {incident_type}
- *Location:* {location}
- *Details:* {summary}

*RESOURCE ALLOCATION:*
{facility_context}

*TASK:* Create a concise emergency dispatch instruction (max 40 words) that includes:
1. Priority level (CRITICAL/HIGH/MEDIUM/LOW)
2. Units to dispatch 
3. Destination
4. Brief tactical note

*FORMAT:* Direct command style, no extra formatting.
"""
        try:
            response = self.llm_model.generate_content(prompt)
            recommendation = response.text.strip().replace('*', '')
            print(f"Allocator    - Generated recommendation")
            return recommendation
        except Exception as e:
            print(f"Allocator    - LLM error: {e}")
            fallback = f"HIGH PRIORITY: Dispatch emergency units to {incident_type.lower()} at {location}."
            if facility_info:
                fallback += f" Route to {facility_info['name']}."
            return fallback

    def _map_priority(self, recommendation: str) -> str:
        """Maps priority from recommendation to UI format."""
        rec_upper = recommendation.upper()
        if "CRITICAL" in rec_upper: return "Critical"
        if "HIGH" in rec_upper: return "High"
        if "MEDIUM" in rec_upper: return "Medium"
        if "LOW" in rec_upper: return "Low"
        return "Medium"

    def _map_severity_from_priority(self, priority: str) -> int:
        """Assigns a severity score based on the priority level."""
        if priority == "Critical": return random.choice([9, 10])
        if priority == "High": return random.choice([7, 8])
        if priority == "Medium": return random.choice([4, 5, 6])
        if priority == "Low": return random.choice([1, 2, 3])
        return 5

    def _extract_assigned_units(self, recommendation: str) -> List[str]:
        """Extracts assigned units from the recommendation text."""
        match = re.search(r"Dispatch (.*?)\b(?:to|at)", recommendation, re.IGNORECASE)
        return [unit.strip() for unit in match.group(1).split(',')] if match else ["Not specified"]
    
    def _map_incident_type(self, incident_type: str) -> str:
        """Maps the internal incident type to the UI-specific type."""
        type_map = {
            "Medical": "medical",
            "Crime": "police",
            "Fire": "fire",
            "Accident": "accident"
        }
        return type_map.get(incident_type, "other")

    def transform_to_ui_format(self, incident_data: Dict[str, Any], processing_result: Dict[str, Any], geocoded_location: Optional[Dict[str, float]]) -> Dict[str, Any]:
        """Transforms the processing result into the desired UI format with dummy data."""
        now_iso = datetime.now(timezone.utc).isoformat()
        recommendation = processing_result.get("ai_recommendation", "")
        priority = self._map_priority(recommendation)
        
        # Add dummy media with a 50% chance of an image
        images, audio, video = [], None, None
        if random.random() < 0.5:
            images.append(f"https://picsum.photos/seed/{uuid.uuid4()}/800/600")
        
        ui_result = {
            "id": uuid.uuid4().int & (1<<31)-1,  # Keep it within a 32-bit integer range
            "title": f"{incident_data.get('incident_type', 'Incident')} at {incident_data.get('location')}",
            "priority": priority,
            "location": geocoded_location if geocoded_location else {"lat": 0.0, "lng": 0.0},
            "address": processing_result.get("nearest_facility", {}).get("address") or incident_data.get("location", "Unknown address"),
            "description": incident_data.get("summary", "No details provided."),
            "timestamp": now_iso,
            "type": self._map_incident_type(incident_data.get("incident_type")),
            "status": 'active',
            "severity": self._map_severity_from_priority(priority),
            "estimatedDuration": "30 minutes",
            "assignedUnits": self._extract_assigned_units(recommendation),
            "contactInfo": {},
            "createdAt": now_iso,
            "updatedAt": now_iso,
            "reportedBy": random.choice(self.dummy_reporters),
            "images": images,
            "audio": audio,
            "video": video,
        }
        return ui_result

    def process_incident(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main incident processing workflow."""
        incident_type = incident_data.get("incident_type")
        summary = incident_data.get("summary")  
        location_text = incident_data.get("location")

        print(f"\nAllocator - Processing {incident_type} incident at '{location_text}'")
        
        geocoded_location = self._geocode_location(location_text)

        service_mapping = {
            "Medical": "hospital emergency room",
            "Crime": "police station",
            "Disaster": "emergency management agency",
            "Fire": "fire station brigade",
            "Accident": "traffic police emergency services"
        }
        
        service_keyword = service_mapping.get(incident_type)
        if not service_keyword:
            raise ValueError(f"Unsupported incident type: {incident_type}")

        facility_info = self._find_nearest_facility(service_keyword, location_text) if geocoded_location else None
        
        call_to_action = self._generate_llm_recommendation(
            incident_type, summary, location_text, facility_info
        )

        processing_result = {
            "ai_recommendation": call_to_action,
            "nearest_facility": facility_info or {"status": "none_found"},
        }
        
        return self.transform_to_ui_format(incident_data, processing_result, geocoded_location)