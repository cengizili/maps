import time
import base64
from seleniumbase import SB
from selenium.webdriver.common.keys import Keys
import re
from urllib.parse import urlparse
import os
from datetime import datetime

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
        scroller = self.sb.find_element("div[class='m6QErb DxyBCb kA9KIf dS8AEf ']")
        self.sb.execute_script("arguments[0].scrollTop = arguments[0].scrollTop + arguments[0].offsetHeight;", scroller)
        time.sleep(0.5)

    def scheduled_scrape(self, run_seconds): 
        start = time.time()
        users = []
        while time.time() < start + run_seconds:
            buttons = self.soup.find_all(lambda tag: tag.name == 'button' and 'al6Kxe' in tag.get('class', []))
            allUsers = [i.next.next for i in buttons]
            divs = self.soup.find_all(lambda tag: tag.name == 'div' and 'DU9Pgb' in tag.get('class', []))
            rates = [i.next.attrs["aria-label"][0] for i in divs]
            users.extend([u for idx, u in enumerate(allUsers) if rates[idx]=='5' and isinstance(u, str)])
            self.scroll_pop_up()
        return list(set(users))

    def run(self, directUrl):
        self.sb.open_new_window(switch_to=True)
        self.sb.get(directUrl)
        # self.sb.save_screenshot("ss")
        self.sb.click_if_visible("button[class='VfPpkd-LgbsSe VfPpkd-LgbsSe-OWXEXe-k8QpJ VfPpkd-LgbsSe-OWXEXe-dgl2Hf nCP5yc AjY5Oe DuMIQc LQeN7 Nc7WLe']", timeout=8)
        self.sb.click("button[class='hh2c6 ']",)
        self.sb.click('button[data-value="Trier"]')
        self.sb.find_element('div[class="fxNQSd"]').send_keys(Keys.ARROW_DOWN, Keys.RETURN)
        time.sleep(1)
        return self.scheduled_scrape(15)
    
    def run2(self, listing):
        self.sb.open_new_window(switch_to=True)
        self.sb.get(listing["url"])
        # self.sb.save_screenshot("ss")
        self.sb.click_if_visible("button[class='VfPpkd-LgbsSe VfPpkd-LgbsSe-OWXEXe-k8QpJ VfPpkd-LgbsSe-OWXEXe-dgl2Hf nCP5yc AjY5Oe DuMIQc LQeN7 Nc7WLe']", timeout=3)
        self.sb.hover("button[jsaction='pane.heroHeaderImage.click']")
        photos = self.soup.find('div', class_='YkuOqf')
        if photos:
            photo_count = photos.next.split("\xa0")[0]
        else:
            photo_count=1
        self.sb.click("button[class='hh2c6 ']",)
        self.sb.find_elements("button[class='g88MCb S9kvJb ']")[1].click()
        self.sb.find_element("input[type='text']",).send_keys("şahane", Keys.ENTER)
        time.sleep(1)
        keyword_count = len(self.soup.find_all(lambda tag: tag.name == 'div' and 'DU9Pgb' in tag.get('class', [])))
        return {"directUrl": [keyword_count, photo_count]}




