### PARALLEL BROWSER WEB SCRAPING USING SELENIUMBASE, FLASK, GOOGLE CLOUD, and TERRAFORM
Here's an implementation for building a scalable application to scrape Google Maps Places by running parallel browsers. 

Let's start with `main.py`, we're starting a new browser session as well as initiating our flask server in the with statement.
This trick is useful because we don't need to create a new browser session for each requests, consecutive requests will be handled on the same browser session.
Since we have only one route, each requests to the server represents same exact operation, which is counting how many reviews include the desired keyword.
Requests have required parameters listing and keyword, the former represents the Google Maps Place on which the specified keyword will be searched. 
The `@retry` decorator enables us to monitor all of the browsers from a single view and check screenshots uploaded to Firebase Storage when an error occurred.

```
@app.route("/keyword_search", methods=['POST'])
@retry(max_retries=3, delay=2)
def keyword_search():
    req = request.get_json()
    return GMB.keyword_search(req["listing"], req["keyword"])
            
with SB(locale_code="US", headed=False,) as sb:
    GMB = GoogleMapsBot(sb)
    app.run(host="0.0.0.0", port=8080)
```
We are going to use Github Actions to automate deploying the flask application to Google Cloud and Terraform to duplicate the server as many times as we want.
This step is essential because a browser session can process only one request at a time and we would like to shard the concurrent requests to the duplicated servers to make sure that all of them will be resulted at one single runtime.
Hence, we can search a keyword on as many places as we want concurrently by scaling the number of duplications.

In the file `functions/main.py`, you can find Firebase Functions to search the desired keywords on the listings retrieved from Serp API. Each keyword-listing match represents a request to deployed servers, 
as (number of keywords)x(number of listings) many as requests are processed concurrently and results are pre-processed before they are saved to Firebase Realtime Database. Distribution of concurrent requests and pre-processing operations
are handled in the `functions/search.py`. Check the code below to have some insights on the Search class.

```
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
```

