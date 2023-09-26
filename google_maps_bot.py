import time
import base64
from seleniumbase import SB
from selenium.webdriver.common.keys import Keys
import re
from urllib.parse import urlparse
import os
from datetime import datetime

def extract(input_string):
    # Define regular expressions to extract a word and a number
    word_pattern = r'\b\w+\b'  # Matches one or more word characters
    number_pattern = r'\d+'
    
    # Use regular expressions to find matches
    word_match = re.search(word_pattern, input_string)
    number_match = re.search(number_pattern, input_string)
    
    # Extract the matched values or return None if no match
    word = word_match.group() if word_match else None
    number = number_match.group() if number_match else None
    
    return word, number

class GoogleMapsBot:

    def __init__(self, sb):
        self.sb = sb
    
    @property
    def soup(self):
       return self.sb.get_beautiful_soup()
        
    @property
    def html(self):
        return self.sb.find_element("//html")

    def scroll_pop_up(self):
        scroller = self.sb.find_element("div[class='m6QErb DxyBCb kA9KIf dS8AEf ']") if self.mode=="reviews" else self.sb.find_element("div[aria-label='Results for restoran']")
        self.sb.execute_script("arguments[0].scrollTop = arguments[0].scrollTop + arguments[0].offsetHeight;", scroller)
        time.sleep(0.5)
    
    def scrape_reviews_to_end(self):
        next = 0
        while True:
            prev = next
            self.scroll_along()
            next = len(self.soup.find_all(lambda tag: tag.name == 'div' and 'DU9Pgb' in tag.get('class', [])))
            if prev == next:
                break
        return next

    def scrape_places_to_limit(self, limit):
        next = 0
        while True:
            prev = next
            self.scroll_along()
            places = [e.attrs["aria-label"] for e in self.soup.find_all('a', {'class': "hfpxzc"})]
            next = len(places)
            if prev == next or next >= limit:
                break
        return places[:limit] if places else []

    def scroll_along(self): 
        start = time.time()
        while time.time() < start + 3:
            self.scroll_pop_up()
    
    def place_search(self, zoom_url, place_limit):
        self.mode = "places"
        self.sb.open_new_window(switch_to=True)
        self.sb.get(zoom_url)
        self.sb.click_if_visible("button[class='VfPpkd-LgbsSe VfPpkd-LgbsSe-OWXEXe-k8QpJ VfPpkd-LgbsSe-OWXEXe-dgl2Hf nCP5yc AjY5Oe DuMIQc LQeN7 Nc7WLe']", timeout=3)
        places = self.scrape_places_to_limit(place_limit)
        return places

    def keyword_search(self, listing, keyword):
        self.mode = "reviews"
        self.sb.open_new_window(switch_to=True)
        self.sb.get(listing["url"])
        # self.sb.save_screenshot("ss")
        self.sb.click_if_visible("button[class='VfPpkd-LgbsSe VfPpkd-LgbsSe-OWXEXe-k8QpJ VfPpkd-LgbsSe-OWXEXe-dgl2Hf nCP5yc AjY5Oe DuMIQc LQeN7 Nc7WLe']", timeout=3)
        self.sb.hover("button[jsaction='pane.heroHeaderImage.click']")
        photos = self.soup.find('div', class_='YkuOqf')
        extract_number = lambda s: re.search(r'\d+', s).group() if re.search(r'\d+', s) else None
        if photos:
            photo_count = int(extract_number(photos.next))
        else:
            photo_count=1
        self.sb.click("button[aria-label*='Reviews']",)
        els = self.sb.find_elements("button[class='e2moi ']")
        extra_keywords = {extract(e.accessible_name)[0]: extract(e.accessible_name)[1] for e in els}
        extra_keywords = {k:int(v) for k,v in extra_keywords.items() if k and v}
        self.sb.find_elements("button[class='g88MCb S9kvJb ']")[1].click()
        time.sleep(1)
        self.sb.find_element("input[type='text']",).send_keys(keyword, Keys.ENTER)
        time.sleep(1)
        keyword_count = self.scrape_reviews_to_end()
        listing.update({"keywords": {keyword: keyword_count}, "photo_count": photo_count, "extra_keywords": extra_keywords})
        return listing




