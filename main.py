
from functools import wraps
from flask import Flask, jsonify, request, send_file
from firebase_admin import initialize_app, db, credentials, messaging, auth, storage
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import InvalidCookieDomainException, NoSuchElementException
import openai
import os
import base64
from fake_useragent import UserAgent
from seleniumbase import SB
from datetime import datetime
import re
import time
import httpx
import asyncio
import json
from google_maps_bot import GoogleMapsBot

app = Flask(__name__)

cred = credentials.Certificate('firebase_credentials.json')

initialize_app(cred, {
    'databaseURL': 'https://instagenie-7cc10-default-rtdb.firebaseio.com/'
})

bucket = storage.bucket('instagenie-7cc10.appspot.com')

def extract_alphanumeric(input_string):
    # Use regular expression to find alphanumeric characters
    alphanumeric = re.sub(r'[^a-zA-Z0-9]', ' ', input_string)
    return alphanumeric

def send_ss(sb, logDate, endpoint, url, e):
    print(f"{e} from {endpoint}")
    sb.save_screenshot("ss")
    path = f'{logDate}/{endpoint}/{extract_alphanumeric(e)}'
    bucket.blob(path).upload_from_filename("ss.png")
    bucket.blob(path).upload_from_string(url)

async def post(data, url, endpoint):
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
            }
        async with httpx.AsyncClient() as client:
            response = await client.post(f'{url}/{endpoint}', headers=headers, data=json.dumps(data), timeout=None)
            return json.loads(response.text)

def log(text):
    asyncio.run(post(text, "https://logger-pfoymczp4q-uc.a.run.app", ""))

def retry(max_retries=3, delay=5):
    def decorator(func):
        @wraps(func)  # Use wraps to preserve the original function's name and docstring
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    result = func(*args, **kwargs)
                    log(f"Successful! {request.url}")
                    return result  # If successful, return the result
                except Exception as e:
                    log(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)} from {request.url}")
                    print(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                    if attempt < max_retries - 1:
                        log(f"Retrying in {delay} seconds... from {request.url}")
                        print(f"Attempt {attempt + 1}/{max_retries}")
                        time.sleep(delay)  # Wait for the specified delay before retrying
                    else:
                        log(f"Max retries reached. Function failed: {str(e)} from {request.url}")
                        print("Max retries reached. Function failed.")
                        pattern = r"serp-\d+"
                        req = request.get_json()
                        send_ss(GMB.sb, req["logDate"], re.search(pattern, request.url).group(), request.url, str(e))
                        l = req["listing"]
                        l.update({req["keyword"]: 0})
                        return l  # If all retries fail, return None
        return wrapper
    return decorator

@app.route("/serp", methods=['POST'])
@retry(max_retries=3, delay=2)
def serp():
    req = request.get_json()
    # print(f"Keyword: {req['keyword']} search for Place: {req['listing']['name']}")
    # log(f"Keyword: {req['keyword']} search for Place: {req['listing']['name']} in {request.url}")
    return GMB.run(req["listing"], req["keyword"])
            
with SB(locale_code="US", headed=False,) as sb:
    GMB = GoogleMapsBot(sb)
    app.run(host="0.0.0.0", port=8080)

# proxy="cengizhanili:UcVwSRNwUM@185.228.195.95:50100" 
        
        

