"""
Vísir news scraper implementation.
"""
import requests
from bs4 import BeautifulSoup
from nl_utils.file_handler import FileType
from .base_scraper import NewsScraper


class VbScraper(NewsScraper):
    def __init__(self, debug_mode=False):
        super().__init__(debug_mode=debug_mode, source_name='vb')
        self.base_url = "https://www.vb.is"

    def get_article_content(self, url):
        """Get the content of a single article"""
        try:
            self.logger.debug("Starting to fetch article from: %s", url)

            # Fetch the page
            response = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }, timeout=10000)
            response.raise_for_status()

            # Save raw HTML for debugging
            if self.debug_mode:
                self.file_handler.save_file(
                    response.text,
                    FileType.TEXT,
                    base_name=f"debug_vb_{self.debug_article_count}"
                )
                self.debug_article_count += 1

            # Parse with html.parser and handle HTML entities
            soup = BeautifulSoup(response.text, 'html.parser')
            self.logger.debug("Created BeautifulSoup object")

            # Extract article text
            self.logger.debug("Extracting article text")
            paragraphs = []

            # Find all paragraph blocks
            paragraph_blocks = soup.find_all('div', class_='paragraph-block')
            if not paragraph_blocks:
                self.logger.debug("No paragraph blocks found")
                return None

            # Process each paragraph block
            for block in paragraph_blocks:
                # Skip if the block is in an ad container
                # Look for specific ad container classes used by VB
                parent = block.find_parent('div', class_=lambda x: x and (
                    'au-wrapper' in x.lower() or
                    'au360' in x.lower() or
                    'oc-adzone' in x.lower() or
                    'ad-wrapper' in x.lower()
                ))
                if parent:
                    self.logger.debug(
                        "Skipping paragraph block in ad container: %s", parent.get('class', []))
                    continue

                # Get all paragraphs in the block
                for p in block.find_all('p'):
                    # Convert HTML entities to proper characters
                    text = p.decode_contents().strip()
                    if text:  # Only include non-empty paragraphs
                        paragraphs.append(text)
                        self.logger.debug("Added paragraph: %s...", text[:50])

            article_text = "\n".join(paragraphs)
            self.logger.debug(
                "Final text length: %d characters", len(article_text))

            return article_text if article_text else None

        except Exception as e:
            self.logger.error(
                "Error fetching article content from %s: %s", url, str(e))
            return None
