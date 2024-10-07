import json
import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import nest_asyncio
import logging
from read import pd_to_file, pd_read_file

nest_asyncio.apply()

#logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def retrieve_product_info(json_file, output_file):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
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
                    await page.goto(url, timeout=20000, )

    
                    title_element = await page.query_selector("#content > main > div:nth-child(2) > div.xs-block > div:nth-child(1) > section.xs-12--none.md-7.xl-8.pdp-core > section > div.MediaGallerySectionstyles__TopWrapper-sc-57tcak-1.fKkMLC > div > h1 > span")
                    title = await title_element.inner_text() if title_element else "Title not found"

                   
                    price_element = await page.query_selector("#content > main > div:nth-child(2) > div.xs-block > div:nth-child(1) > section.xs-12--none.md-5--none.xl-4--none.pdp-right > section > ul > li > h2")
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
        pd_to_file(df, output_file, index=False)
        logging.info(f"Data saved to {output_file}")

if __name__ == "__main__":
    json_input_file = 'tmp/argos.json'
    output_csv_file = 'tmp/argos.csv'
    asyncio.run(retrieve_product_info(json_input_file, output_csv_file))