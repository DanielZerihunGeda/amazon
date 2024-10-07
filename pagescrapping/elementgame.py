import json
import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import nest_asyncio
import logging
from read import pd_to_file, pd_read_file

nest_asyncio.apply()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def retrieve_product_info(json_file='tmp/elementgame.json', output_file='tmp/elementgame.tsv'):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Load the URLs from the JSON file
        with open(json_file, 'r', encoding='utf-8') as f:
            urls = json.load(f)

        results = []

        for url in urls:
            retries = 3
            while retries > 0:
                try:
                    logging.info(f"Navigating to {url}")
                    await page.goto(url, timeout=60000)

    
                    title_element = await page.query_selector("body > div.section-colored.text-center > div > div.product-wrap.row > div.product-info.col-xs-12.col-sm-12.col-md-7.col-lg-7 > div > div > h1")
                    title = await title_element.inner_text() if title_element else "Title not found"

                   
                    price_element = await page.query_selector("#testproduct > div > div.price-wrap > span.currentPrice")
                    price = await price_element.inner_text() if price_element else "price not found"
                    results.append({"url": url, "product_title": title, "price": price})
                    logging.info(f"Retrieved: {title} - {price}")
                    break

                except Exception as e:
                    retries -= 1
                    logging.error(f"Error retrieving information from {url}: {e}. Retries left: {retries}")
                    if retries == 0:
                        results.append({"url": url, "product_title": "Error", "price": "Error"})

        await browser.close()

        df = pd.DataFrame(results)
        pd_to_file(df, output_file)
        logging.info(f"Data saved to {output_file}")