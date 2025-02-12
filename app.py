import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
#from config import GOOGLE_API_KEY, YELP_API_KEY  # Import API keys from config
import json
import os

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
YELP_API_KEY = os.getenv('YELP_API_KEY')

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# API URLs
GOOGLE_API_URL = 'https://places.googleapis.com/v1/places:searchNearby'
GOOGLE_DETAILS_URL = 'https://places.googleapis.com/v1/places/'
GOOGLE_GEOCODE_URL = 'https://maps.googleapis.com/maps/api/geocode/json'
YELP_API_URL = 'https://api.yelp.com/v3/businesses/search'

# Function to fetch coordinates from location
def get_coordinates(location):
    params = {
        'address': location,
        'key': GOOGLE_API_KEY
    }
    response = requests.get(GOOGLE_GEOCODE_URL, params=params)
    #print(f"Geocode API Response: {response.status_code} - {response.text}")  # Debug
    if response.status_code == 200:
        results = response.json().get('results')
        if results:
            location_data = results[0]['geometry']['location']
            return location_data['lat'], location_data['lng']
    return None, None

# Function to fetch steak restaurants from Google Places (New API)
def find_steak_restaurants_google(location, radius):
    latitude, longitude = get_coordinates(location)
    if latitude is None or longitude is None:
        print("Failed to get coordinates for the location.")
        return []

    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': GOOGLE_API_KEY,
        'X-Goog-FieldMask': '*'
    }

    payload = {
        'locationRestriction': {
            'circle': {
                'center': {
                    'latitude': latitude,
                    'longitude': longitude
                },
                'radius': radius  # Dynamic radius based on user input
            }
        },
        'includedPrimaryTypes': ['steak_house']
    }

    #print(f"Sending Google Places API Request with payload: {payload}")  # Debug
    response = requests.post(GOOGLE_API_URL, headers=headers, json=payload)
    #print(f"Google Places API Response: {response.status_code} - {response.text}")  # Debug

    # Exporting the Google API response to a file
    if response.status_code == 200:
        #with open('google_places_api_response.json', 'w') as file:
            #json.dump(response.json(), file, indent=4)

        places = response.json().get('places', [])
        detailed_results = []

        for place in places[:10]:  # Limit API calls to top 10 results
            detailed_results.append({
                'name': place.get('displayName', {}).get('text', 'Unknown'),
                'rating': place.get('rating', 0),
                'address': place.get('formattedAddress', 'N/A'),
                'website': place.get('websiteUri', '#'),
                'maps_link': place.get('googleMapsUri', '#'),
                'phone': place.get('internationalPhoneNumber', 'N/A'),
                'open_now': place.get('currentOpeningHours', {}).get('openNow', False)
            })

        return detailed_results
    return []

# Unified search function with fallback and sorting by rating
def find_steak_restaurants(location, radius):
    #print(f"Searching for steak restaurants in: {location} with radius: {radius}")  # Debug
    restaurants = find_steak_restaurants_google(location, radius)
    restaurants_sorted = sorted(restaurants, key=lambda x: x['rating'], reverse=True)
    #print(f"Sorted Results: {restaurants_sorted}")  # Debug
    return restaurants_sorted[:5]

# Basic chatbot interaction
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    location = data.get('location')
    radius = data.get('radius', 1000)  # Default to 1 km if not provided

    #print(f"Received location: {location}, radius: {radius}")  # Debug

    if location:
        restaurants = find_steak_restaurants(location, radius)
        return jsonify({'restaurants': restaurants})
    else:
        return jsonify({'reply': 'Please provide your location to find steakhouses.'})
        
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))  # Default to 10000 if PORT isn't set
    app.run(host='0.0.0.0', port=port)


