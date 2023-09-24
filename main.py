
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
from google_maps_bot import GoogleMapsBot
app = Flask(__name__)

def retry(max_retries=3, delay=5):
    def decorator(func):
        @wraps(func)  # Use wraps to preserve the original function's name and docstring
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    result = func(*args, **kwargs)
                    return result  # If successful, return the result
                except Exception as e:
                    print(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                    if attempt < max_retries - 1:
                        print(f"Retrying in {delay} seconds...")
                        time.sleep(delay)  # Wait for the specified delay before retrying
                    else:
                        print("Max retries reached. Function failed.")
                        return jsonify(f"{str(e)} from {request.url}")  # If all retries fail, return None
        return wrapper
    return decorator

@app.route("/serp", methods=['POST'])
@retry(max_retries=3, delay=5)
def serp():
    req = request.get_json()
    print(f"Keyword: {req['keyword']} search for Place: {req['listing']['name']}")
    return GMB.run(req["listing"], req["keyword"])
            
with SB(locale_code="US", headed=False,) as sb:
    GMB = GoogleMapsBot(sb)
    app.run(host="0.0.0.0", port=8080)

# proxy="cengizhanili:UcVwSRNwUM@185.228.195.95:50100" 
        
        

