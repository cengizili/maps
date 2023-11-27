from googlemaps import Client
import math
import requests
import urllib.parse
import re
import time 
from serpapi import GoogleSearch


client = Client(key = "XXX")

def extractor(share_url):
    r = requests.head(share_url, allow_redirects=True)    
    match = re.search(r"/place/(.*?)/@([\d.]+),([\d.]+),([\d.]+)", r.url)
    lat = match.group(2)
    lng = match.group(3)
    zoom = match.group(4)
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
    all_fields = ['business_status', 'formatted_address','geometry/location','name', 
              'place_id', 'rating','types', 'user_ratings_total']
    place_details = client.find_place(input = place_name, # or enter a phone number
                                    input_type = 'textquery', # or 'phonenumber'
                                    location_bias = location_bias, 
                                    fields = all_fields)
    loc = place_details["candidates"][0]["geometry"]["location"]
    return loc["lat"], loc["lng"], place_details

def get_listings(short_url, nearbyQuery, zoom_levels):
    lat,lng, place_details = real_locations(extractor(short_url))
    token = None
    listings = []
    urls = [f"https://www.google.com/maps/search/{nearbyQuery}/@{lat},{lng},{z}z?entry=ttu" for z in zoom_levels]
    while True:
        desirable_places = client.places(query = nearbyQuery, location=f"{lat},{lng}", page_token=token)
        token = desirable_places.get("next_page_token", None)
        listings.extend(sorted(desirable_places["results"], key=lambda item: sort_key(item, lat, lng)))
        time.sleep(2)
        if listings[-1]["distance_meters"]>=400*(2**(20-min(zoom_levels))) or token==None:
            return listings, urls

def get_locals_zoom(lat, lng, nearbyQuery, zoom_level, placeLimit):
    results = []
    for x in range(max(1, placeLimit//20)):
        params = {
        "engine": "google_maps",
        "q": nearbyQuery,
        "ll": f"@{lat},{lng},{zoom_level}z",
        "type": "search",
        "api_key": "6399744a97a0542c38e836e813d5de832e729c1f3b6ea99da4ff67ffa02bd987"
        }
        search = GoogleSearch(params)
        local_results = search.get_dict()["local_results"]
        results.append(local_results)
    for l in local_results:
        l["url"] = f"https://www.google.com/maps/search/?api=1&query={l['gps_coordinates']['latitude']},{l['gps_coordinates']['longitude']}&query_place_id={l['place_id']}"
    return local_results[:placeLimit]

def get_locals(shortUrl, nearbyQuery, zoom_levels, placeLimit):
    lat,lng, place_details = real_locations(extractor(shortUrl))
    place_details["url"] = f"https://www.google.com/maps/search/?api=1&query={lat},{lng}&query_place_id={place_details['candidates'][0]['place_id']}"
    urls = [f"https://www.google.com/maps/search/{nearbyQuery}/@{lat},{lng},{z}z?entry=ttu" for z in zoom_levels]
    locals = [get_locals_zoom(lat, lng, nearbyQuery, zoom_level, placeLimit) for zoom_level in zoom_levels]
    for sub in locals:
        sub.insert(0, place_details['candidates'][0])
    return locals, urls
        



