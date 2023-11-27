# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`

from firebase_functions import https_fn
from firebase_admin import initialize_app, credentials, db
import sys
from pathlib import Path
sys.path.insert(0, Path(__file__).parent.as_posix())
import gmaps
import asyncio
import json
import httpx
from functools import partial
import re
import json
from collections import defaultdict
from datetime import datetime
import itertools
import random  
from difflib import SequenceMatcher
from search import Search

cred = credentials.Certificate('firebase_credentials.json')
f_app = initialize_app(cred, {
    "databaseURL": "https://XXXX-default-rtdb.firebaseio.com/"
})

queriesRef = db.reference("queries")

def extract_alphanumeric(input_string):
    alphanumeric = re.sub(r'\W', ' ', input_string)
    return alphanumeric

@https_fn.on_request(max_instances=10, timeout_sec=300)
def logger(req: https_fn.Request) -> https_fn.Response:
    request = req.get_json()
    print(request)
    return json.dumps({"data": "OK"})
    
@https_fn.on_request(max_instances=3, timeout_sec=300, cpu=2, memory=2048)
def categoryBasedSearch(req: https_fn.Request) -> https_fn.Response:

    request = req.get_json()

    search = Search (
        keywords= request["keywords"], # list of desired keywords
        shareUrl=request["shareUrl"], # location of the pivot place to search nearbyQuery
        nearbyQuery=request["nearbyQuery"], # specifies a query on the pivot location to get local listings
        zoomLevels=request["zoomLevels"], # same query on different zoom levels
        placeLimit=request["placeLimit"], # how many listings will be retrieved from Serp API
        maxServices=100, # must be equal to the number of duplicated servers on Google Cloud
        maxInstances=3,  # gives the maximum concurrent requests that can be processed when it multiplied with maxServices
    )

    search.run()

    queryRef = queriesRef.push()
    queryRef.set({
        "shareUrl": request["shareUrl"],
        "nearbyQuery": request["nearbyQuery"],
        "pivot": search.pivot,
        "dateCreatedUTC": search.logDate,
        "places": search.places_modified
    })

    return json.dumps(search.places)

@https_fn.on_request(max_instances=3, timeout_sec=300, cpu=2, memory=2048)
def directSearch(req: https_fn.Request) -> https_fn.Response:

    request = req.get_json()

    search = Search(
        keywords= [request["keyword"]],
        shareUrl=request["shareUrl"],
        nearbyQuery=request["keyword"],
        zoomLevels=request["zoomLevels"],
        placeLimit=request["placeLimit"],
        maxServices=100,
        maxInstances=3,
    )

    search.run()

    queryRef = queriesRef.push()
    queryRef.set({
        "shareUrl": request["shareUrl"],
        "pivot": search.pivot,
        "dateCreatedUTC": search.logDate,
        "keyword": request['keyword'],
        "places": search.places_modified
    })

    return json.dumps(search.places)
