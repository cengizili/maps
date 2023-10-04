from datetime import datetime
import gmaps
from functools import partial
import asyncio
import httpx
import json
import itertools

class Search:

    def __init__(self, shareUrl, nearbyQuery, maxServices, maxInstances, keywords, placeLimit, zoomLevels) -> None:
        self.maxServices = maxServices
        self.shareUrl = shareUrl
        self.maxInstances = maxInstances
        self.keywords = keywords
        self.placeLimit = placeLimit
        self.nearbyQuery = nearbyQuery
        self.zoomLevels = zoomLevels
        self.logDate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    async def post(self, data, url, endpoint):
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
            }
        async with httpx.AsyncClient() as client:
            response = await client.post(f'{url}/{endpoint}', headers=headers, data=json.dumps(data), timeout=None)
            try:
                return json.loads(response.text)
            except:
                return None
        
    async def run_tasks(self, partial_funcs):
        tasks = [func() for func in partial_funcs]
        return await asyncio.gather(*tasks)

    def match(self, e, listings):
        for l in listings:
            if l["place_id"]==e["place_id"]:
                return l, listings.index(l)
        return None

    def update_dict(self, dict, entry):
        dict.update(entry)
        return dict

    def merge_places(self, places, keywords):
        unique_places = list({p["place_id"]:p for p in places if p is not None and p.get("keywords", None)}.values())
        for u in unique_places:
            for p in places:
                if p and u["place_id"]==p["place_id"]:
                    u["keywords"].update(p["keywords"])
            for k in keywords:
                if not u["keywords"].get(k, False):
                    u["keywords"].update({k:0})
        return unique_places
    
    def get_top_listings(self, keyword, listings):
        ordered = [l["keywords"][keyword] for l in listings]
        print(ordered)
        idxs = [idx for idx, i in enumerate(ordered) if i==max(ordered)]
        print(idxs)
        return [listings[idx] for idx in idxs]

    def getSerpPlaces(self):
        self.local_results, self.urls = gmaps.get_locals(self.shareUrl, self.nearbyQuery, self.zoomLevels, self.placeLimit)
        self.pivot = self.local_results[0][0]
        self.unique_listings = list({l["place_id"]:l for l in [i for sub in self.local_results for i in sub]}.values())
        
    def scaleData(self):
        self.load = len(self.unique_listings)*len(self.keywords)
        self.limit = self.maxServices * self.maxInstances
        if self.limit < self.load:
            self.unique_listings = [l for idx, l in enumerate(self.unique_listings) if (idx+1)*len(self.keywords) <= self.limit]
        
        self.services = [f"https://serp-{i}-g7tfezwnhq-uc.a.run.app" for i in range(self.maxServices) for j in range(self.maxInstances)]
        self.data_zip = {idx: {"listing": l, "keyword": k, "service": self.services[idx], "logDate": self.logDate} for idx, (l, k) in enumerate(list(itertools.product(self.unique_listings, self.keywords)))}
    
    def getPlaces(self):
        partial_funcs = [partial(self.post, data=self.data_zip[idx], url = self.data_zip[idx]["service"], endpoint="keyword_search") for idx in range(len(self.data_zip))]
        responses = asyncio.run(self.run_tasks(partial_funcs))
        self.places = self.merge_places(responses, self.keywords)

        for p in self.places:
            p["rankings"] = {z:{} for z in self.zoomLevels}
            if p["place_id"] != self.pivot["place_id"]:
                p.pop("position")
            for idx, z in enumerate(self.zoomLevels):
                for k in self.keywords:
                    k_sorted = sorted([self.match(l, self.places)[0] for l in self.local_results[idx] if self.match(l, self.places)], key=lambda x: x["keywords"][k], reverse=True)
                    if self.match(p, k_sorted): p["rankings"].update({z: {k: self.match(p, k_sorted)[1]}})
                    local_match = self.match(p, self.local_results[idx])
                    if p["place_id"]==self.pivot["place_id"]:
                        self.pivot = p
                    elif local_match:
                        p["rankings"][z].update({"listing": local_match[1]})
        
        self.places_modified = {z:{idx2: self.match(l, self.places)[0] for idx2, l in enumerate(self.local_results[idx]) if self.match(l, self.places) and l["place_id"]!=self.pivot["place_id"]} for idx, z in enumerate(self.zoomLevels)}

            
    def run(self):
        self.getSerpPlaces()
        self.scaleData()
        self.getPlaces()
