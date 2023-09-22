"""This script serves as an example on how to use Python 
   & Playwright to scrape/extract data from Google Maps"""

from playwright.sync_api import sync_playwright
from dataclasses import dataclass, asdict, field
import pandas as pd
import argparse
import re
import time
import sys


@dataclass
class Business:
    """holds business data"""

    name: str = None
    address: str = None
    website: str = None
    phone_number: str = None
    photos_count: int = 0
    reviews_count: int = 0
    reviews_average: float = 0.0
    keyword_count: int = 0


@dataclass
class BusinessList:
    """holds list of Business objects,
    and save to both excel and csv
    """

    business_list: list[Business] = field(default_factory=list)

    def dataframe(self):
        """transform business_list to pandas dataframe

        Returns: pandas dataframe
        """
        return pd.json_normalize(
            (asdict(business) for business in self.business_list), sep="_"
        )

    def save_to_excel(self, filename):
        """saves pandas dataframe to excel (xlsx) file

        Args:
            filename (str): filename
        """
        self.dataframe().to_excel(f"{filename}.xlsx", index=False)

    def save_to_csv(self, filename):
        """saves pandas dataframe to csv file

        Args:
            filename (str): filename
        """
        self.dataframe().to_csv(f"{filename}.csv", index=False)


def main(zoom):
    print(f"zoom: {zoom}")

    page.goto(search_url, timeout=60000)
    # wait is added for dev phase. can remove it in production
    page.wait_for_timeout(1000)
    
    #get main company info
    if(zoom == 14):
        print('get main info')
        company_name = page.locator('h1').inner_text()
        company_photos = page.locator('div[role=main] > div button').nth(1).inner_text()
        company_photos = company_photos.replace(".", "")
        company_photos_counts = re.search(r'\d+', company_photos)
        if(company_photos_counts.span()):
            company_photos_count = company_photos_counts.group(0)
        else:
            company_photos_count = 0
        print(f"COMPANY NAME: {company_name}")
        print(f"COMPANY PHOTOS: {company_photos}")
        print(f"COMPANY PHOTOS COUNT: {company_photos_count}")


    #search
    page.locator('//input[@id="searchboxinput"]').fill(search_for)
    page.wait_for_timeout(1000)

    page.keyboard.press("Enter")
    page.wait_for_timeout(3000)
    
    #echo url
    current_url = page.url
    print(f"Page URL: {current_url}")
    current_url = re.sub(r'\d+z\/', f"{zoom}z/", current_url, flags=re.IGNORECASE)
    print(f"NEW URL: {current_url}")
    page.goto(current_url, timeout=60000)
    # wait is added for dev phase. can remove it in production
    page.wait_for_timeout(1000)
    
    # scrolling
    page.hover('//a[contains(@href, "https://www.google.com/maps/place")]')

    # this variable is used to detect if the bot
    # scraped the same number of listings in the previous iteration
    previously_counted = 0
    while True:
        page.mouse.wheel(0, 10000)
        page.wait_for_timeout(1000)

        if (
            page.locator(
                '//a[contains(@href, "https://www.google.com/maps/place")]'
            ).count()
            >= total
        ):
            listings = page.locator(
                '//a[contains(@href, "https://www.google.com/maps/place")]'
            ).all()[:total]
            listings = [listing.locator("xpath=..") for listing in listings]
            print(f"Total Scraped: {len(listings)}")
            #print(f"Listings: {listings}")
            break
        else:
            # logic to break from loop to not run infinitely
            # in case arrived at all available listings
            if (
                page.locator(
                    '//a[contains(@href, "https://www.google.com/maps/place")]'
                ).count()
                == previously_counted
            ):
                listings = page.locator(
                    '//a[contains(@href, "https://www.google.com/maps/place")]'
                ).all()
                print(f"Arrived at all available\nTotal Scraped: {len(listings)}")
                break
            else:
                previously_counted = page.locator(
                    '//a[contains(@href, "https://www.google.com/maps/place")]'
                ).count()
                print(
                    f"Currently Scraped: ",
                    page.locator(
                        '//a[contains(@href, "https://www.google.com/maps/place")]'
                    ).count(),
                )

    business_list = BusinessList()

    # scraping
    for listing in listings:
        listing.click()
        page.wait_for_timeout(5000)

        name_xpath = '//div[contains(@class, "fontHeadlineSmall")]'
        address_xpath = '//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]'
        website_xpath = '//a[@data-item-id="authority"]//div[contains(@class, "fontBodyMedium")]'
        phone_number_xpath = '//button[contains(@data-item-id, "phone:tel:")]//div[contains(@class, "fontBodyMedium")]'
        photos_xpath = 'button[jsaction="pane.heroHeaderImage.click"]'
        reviews_span_xpath = '//span[@role="img"]'
        reviews_tab_xpath = 'button[data-tab-index="1"]'
        reviews_tab_search_xpath = 'input.fontBodyLarge'
        reviews_tab_review = 'div[data-review-id].fontBodyMedium'

        business = Business()

        if listing.locator(name_xpath).count() > 0:
            business.name = listing.locator(name_xpath).inner_text()
        else:
            business.name = ""
        if page.locator(address_xpath).count() > 0:
            business.address = page.locator(address_xpath).inner_text()
        else:
            business.address = ""
        if page.locator(website_xpath).count() > 0:
            business.website = page.locator(website_xpath).inner_text()
        else:
            business.website = ""
        if page.locator(phone_number_xpath).count() > 0:
            business.phone_number = page.locator(phone_number_xpath).inner_text()
        else:
            business.phone_number = ""
        if page.locator(photos_xpath).count(): 
            business_photos = page.locator(photos_xpath).locator('..').locator('..').locator('button').nth(1).inner_text()
            print(business_photos)
            business_photos = business_photos.replace(".", "")
            business_photos_counts = re.search(r'\d+', business_photos)
            print(business_photos_counts)
            if(business_photos_counts.span()):
                business.photos_count = business_photos_counts.group(0)
            else:
                business.photos_count = 0
        else:
            business.photos_count = 0
        if listing.locator(reviews_span_xpath).count() > 0:
            business.reviews_average = float(
                listing.locator(reviews_span_xpath).nth(0)
                .get_attribute("aria-label")
                .split()[0]
                .replace(",", ".")
                .strip()
            )
            business.reviews_count = int(
                listing.locator(reviews_span_xpath).nth(0)
                .get_attribute("aria-label")
                .split()[2]
                .replace(".", "")
                .strip()
            )
        else:
            business.reviews_average = ""
            business.reviews_count = 0
        business.keyword_count = 0
        if page.locator(reviews_tab_xpath).count() > 0:
            page.locator(reviews_tab_xpath).click()
            page.locator(reviews_tab_search_xpath).click()
            page.wait_for_timeout(1000)
            page.locator(reviews_tab_search_xpath).type(search_for)
            page.wait_for_timeout(1000)
            page.locator(reviews_tab_search_xpath).press('Enter')
            page.wait_for_timeout(3000)
            #time.sleep(3)
            
            """
            page.mouse.wheel(0, 10000)
            page.wait_for_timeout(1000)
            page.mouse.wheel(0, 10000)
            page.wait_for_timeout(1000)
            page.mouse.wheel(0, 10000)
            page.wait_for_timeout(10000)
            """
            for i in range(sys.maxsize): #make the range as long as needed
                reviews_count_initial = page.locator(reviews_tab_review).count()
                print(f'Initial reviews count {reviews_count_initial}')
                page.mouse.wheel(0, 15000)
                #time.sleep(2)
                page.wait_for_timeout(2000)
                reviews_count_new = page.locator(reviews_tab_review).count()
                print(f'New reviews count {reviews_count_new}')
                if reviews_count_new == reviews_count_initial:
                    business.keyword_count = reviews_count_new
                    break
                i += 1
            
            #infinite scroll
            """
            prev_page_height = page.evaluate("document.body.scrollHeight") 
            print(f'Initial page height {prev_page_height}')

            # scroll down
            while True:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                page.wait_for_timeout(1000)   # giving some time to load the page
                        
                cur_page_height = page.evaluate("document.body.scrollHeight")
                print(f'Current page height {cur_page_height}')
                        
                if cur_page_height > prev_page_height:
                    prev_page_height = cur_page_height
                elif cur_page_height == prev_page_height:
                    break
            """

        business_list.business_list.append(business)

    # saving to both excel and csv just to showcase the features.
    #print(business_list)
    # business_list.save_to_excel(f"{zoom}-google_maps_data")
    business_list.save_to_csv(f"{zoom}-google_maps_data")

    main.url = current_url
    # browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--url", type=str)
    parser.add_argument("-s", "--search", type=str)
    parser.add_argument("-t", "--total", type=int)
    args = parser.parse_args()

    if args.url:
        search_url = args.url
    else:
        # in case no arguments passed
        # the scraper will search by defaukt for:
        search_url = "https://goo.gl/maps/8jbwbWnu6uKqM1q7A"

    if args.search:
        search_for = args.search
    else:
        # in case no arguments passed
        # the scraper will search by default for:
        search_for = "restoran"

    # total number of products to scrape. Default is 3
    if args.total:
        total = args.total
    else:
        total = 3
        
    #start browser
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False) # start the browser
        browser_context = browser.new_context() # new 'incognito' window
        browser_context.add_cookies([{'name': 'CONSENT', 'value': 'YES+cb.20210720-07-p0.en+FX+410', 'domain': 'www.google.com', 'path': '/'}])
        page = browser_context.new_page() # open a new tab

        main(14)
        #echo final url
        #print(f"14 FINAL URL: {main.url}")
        search_url = main.url
        main(15)
        search_url = main.url
        main(16)
        search_url = main.url
        main(17)
        
        browser.close()
