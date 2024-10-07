import asyncio
import json
import logging
import fire
from playwright.async_api import async_playwright

class WaylandGamesScraper:
    def init(self):
        self.data = []
        self.delay = 20  # seconds

    async def navigate_and_scrape(self, page, url):
        await page.goto(url)
        await page.wait_for_timeout(self.delay * 1000)  # Wait for the page to load

        # Extract data
        title = await page.query_selector_text('#next > main > section > div > div.LayoutCategory_titleAreafmWIa > h1')
        articles = await page.query_selector_all('#__next > main > section > section > div > article > div > article > div')
        headers = await page.query_selector_all('#__next > main > section > header > div > div > div > div > div > div > div > div > p')
        product_titles = await page.query_selector_all('#next > main > section > div > div > section > div > header > div > div.ProductInfo_detailHeadK0vW5 > h1 > span')
        product_prices = await page.query_selector_all('#next > main > section > div > div > section > div > header > div > div.ProductInfo_detailPricezV7Kq > div > span.Price_pricesfl_r.Price_priceNowOV_3o.stripo-price')
        panels = await page.query_selector_all('#panel--\\:r5\\:--0 > div')
        tables = await page.query_selector_all('#panel--\\:r5\\:--1 > div > table > tbody')

        # Store data in a nested key-value JSON format
        self.data.append({
            "title": title,
            "articles": [await article.inner_text() for article in articles],
            "headers": [await header.inner_text() for header in headers],
            "product_titles": [await product_title.inner_text() for product_title in product_titles],
            "product_prices": [await product_price.inner_text() for product_price in product_prices],
            "panels": [await panel.inner_text() for panel in panels],
            "tables": [await table.inner_text() for table in tables]
        })

        # Navigate to the next page
        next_button = await page.query_selector('#next > div.Nav_navWrapperu4Z6J > div > nav > ul > li:last-child > a')
        if next_button:
            next_url = await next_button.get_attribute('href')
            if next_url:
                await self.navigate_and_scrape(page, next_url)

    async def run(self, start_url):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                await self.navigate_and_scrape(page, start_url)
            except Exception as e:
                logging.error(f"An error occurred: {e}")
            finally:
                await browser.close()

    def get_data(self):
        return self.data

    def save_data(self, filename='data.json'):
        with open(filename, 'w') as f:
            json.dump(self.data, f, indent=4)

def main(start_url):
    scraper = WaylandGamesScraper()
    asyncio.run(scraper.run(start_url))
    scraper.save_data()

if name == "main":
    fire.Fire(main)