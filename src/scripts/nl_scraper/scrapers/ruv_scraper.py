"""
RUV news scraper implementation.
"""
import json
import re
import requests
from bs4 import BeautifulSoup
from .base_scraper import NewsScraper


class RUVScraper(NewsScraper):
    def __init__(self, debug_mode=False):
        super().__init__(debug_mode=debug_mode, source_name='ruv')
        self.base_url = "https://www.ruv.is"

    def get_article_content(self, url):
        """Get the content of a single article from RUV"""
        try:
            self.logger.debug("Starting to fetch article from: %s", url)

            # Fetch the page
            response = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }, timeout=10000)
            response.raise_for_status()

            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find the JSON data in the script tag
            script_tag = soup.find('script', {'id': '__NEXT_DATA__'})
            if not script_tag:
                self.logger.debug("Could not find __NEXT_DATA__ script tag")
                return None

            # Parse the JSON data
            json_data = json.loads(script_tag.string)

            # Navigate to the article body text
            try:
                body_blocks = json_data['props']['pageProps']['data']['article']['body']
                article_text = []

                for block in body_blocks:
                    if block['block_type'] == 'text_block' and block['text_block'] and block['text_block']['html']:
                        # Clean the HTML content
                        text = block['text_block']['html']
                        # Remove HTML tags
                        text = re.sub(r'<[^>]+>', '', text)
                        # Remove extra whitespace
                        text = ' '.join(text.split())
                        if text:
                            article_text.append(text)

                return ' '.join(article_text)

            except (KeyError, TypeError) as e:
                self.logger.debug("Error extracting article text: %s", str(e))
                return None

        except Exception as e:
            self.logger.debug("Error fetching article: %s", str(e))
            return None
