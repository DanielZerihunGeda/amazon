from urllib.parse import urljoin
from playwright.async_api import async_playwright
import asyncio
import nest_asyncio
import json
import logging
import fire

logging.basicConfig(level=logging.DEBUG)

class WebScraper:
    def __init__(self, start_url, link_selector, subsequent_link_selector, max_initial_links):
        self.start_url = start_url
        self.link_selector = link_selector
        self.subsequent_link_selector = subsequent_link_selector 
        self.max_initial_links = max_initial_links
        self.visited_urls = set()
        self.final_links = set()
        self.stack = [] 

    async def scrape(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                await self._scrape_page(page, self.start_url)  
            except Exception as e:
                logging.error(f"Error during scraping: {e}")
            finally:
                await browser.close()
                self.save_to_json('tmp/final_links.json')

    async def _scrape_page(self, page, url):
        self.stack.append(url)
        initial_links_count = 0
        is_first_page = True
        
        while self.stack:
            current_url = self.stack.pop()

            if current_url in self.visited_urls:
                continue

            try:
                logging.info(f"Navigating to {current_url}")
                await page.goto(current_url, timeout=60000)

                if is_first_page:
                    logging.info(f"Waiting for initial selector {self.link_selector}")
                    await page.wait_for_selector(self.link_selector, timeout=20000)

                    links = await page.query_selector_all(f"{self.link_selector} a")
                    logging.info(f"Found {len(links)} links on {current_url}")

                    links = links[:self.max_initial_links]
                    is_first_page = False 
                    for link in links:
                        href = await link.get_attribute('href')
                        if href:
                            full_url = urljoin(self.start_url, href)
                            if full_url not in self.visited_urls:
                                self.stack.append(full_url)
                                logging.info(f"Added initial link to stack: {full_url}")
                else:

                    logging.info(f"Waiting for subsequent selector {self.subsequent_link_selector}")
                    await page.wait_for_selector(self.subsequent_link_selector, timeout=20000)
                    

                    links = await page.query_selector_all(f"{self.subsequent_link_selector} a")
                    logging.info(f"Found {len(links)} subsequent links on {current_url}")

                    if not links:
                        logging.info(f"No more links on {current_url}, adding to final links")
                        self.final_links.add(current_url)
                        self.visited_urls.add(current_url)
                    else:
                 
                        for link in links:
                            href = await link.get_attribute('href')
                            if href:
                                full_url = urljoin(self.start_url, href)
                                if full_url not in self.visited_urls:
                                    self.final_links.add(full_url)
                                    logging.info(f"Retrieved link: {full_url}")

                logging.info(f"Current stack size: {len(self.stack)}")

            except Exception as e:
                logging.error(f"An error occurred while scraping {current_url}: {e}")

    def save_to_json(self, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(list(self.final_links), f, ensure_ascii=False, indent=4)
        logging.info(f"Data saved to {filename}")
def main(start_url, link_selector, subsequent_link_selector, max_initial_links):
    nest_asyncio.apply()  # To allow asyncio.run inside Jupyter notebooks
    scraper = WebScraper(start_url, link_selector, subsequent_link_selector, max_initial_links)
    asyncio.run(scraper.scrape())

if __name__ == "__main__":
    fire.Fire(main)
