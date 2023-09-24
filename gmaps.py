from googlemaps import Client
import math
import requests
import urllib.parse
import re
import time 

client = Client(key = "AIzaSyCCJMgAPVB74U_cWnhXsqTtU6x5xCUYuKs")

def extractor(share_url):
    r = requests.head(share_url, allow_redirects=True)
    pattern = r"@([-0-9.]+),([-0-9.]+),([0-9]+)z"
    match = re.search(pattern, r.url)
    lat = match.group(1)
    lng = match.group(2)
    zoom_level = match.group(3)
    # Decode the place name from the path
    path_segments = urllib.parse.urlparse(r.url).path.split("/")
    place_name = urllib.parse.unquote(path_segments[3])
    return place_name, lat, lng

    
def haversine(lat1, lon1, lat2, lon2):
    # Radius of the Earth in km
    R = 6371.0
    
    # Convert latitude and longitude from degrees to radians
    lat1 = math.radians(float(lat1))
    lon1 = math.radians(float(lon1))
    lat2 = math.radians(float(lat2))
    lon2 = math.radians(float(lon2))
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    
    return distance

def sort_key(item, base_lat, base_lng):
    lat2 = item['geometry']['location']['lat']
    lng2 = item['geometry']['location']['lng']
    distance = haversine(base_lat, base_lng, lat2, lng2)
    item['distance_meters'] = distance*1000
    item["url"] = f"https://www.google.com/maps/search/?api=1&query={lat2},{lng2}&query_place_id={item['place_id']}"
    return distance

def real_locations(params):
    place_name, lat, lng = params
    location_bias = f'circle:{500}@{lat},{lng}'# lat lon of The White House

    place_details = client.find_place(input = place_name, # or enter a phone number
                                    input_type = 'textquery', # or 'phonenumber'
                                    location_bias = location_bias, 
                                    fields = ["geometry/location",])
    loc = place_details["candidates"][0]["geometry"]["location"]
    return loc["lat"], loc["lng"]

def get_listings(short_url, radius):
    lat,lng = real_locations(extractor(short_url))
    token = None
    listings = []
    while True:
        desirable_places = client.places(query = 'restoran', location=f"{lat},{lng}", page_token=token)
        token = desirable_places.get("next_page_token", None)
        listings.extend(sorted(desirable_places["results"], key=lambda item: sort_key(item, lat, lng)))
        time.sleep(2)
        if listings[-1]["distance_meters"]>=radius or token==None:
            return [l for l in listings if l["distance_meters"]<=radius]
        
# lt = get_listings('https://goo.gl/maps/8jbwbWnu6uKqM1q7A', 15)
# pass