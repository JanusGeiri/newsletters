"""
Visir news scraper implementation.
"""
import requests
from bs4 import BeautifulSoup
from nl_utils.file_handler import FileType
from .base_scraper import NewsScraper


class VisirScraper(NewsScraper):
    def __init__(self, debug_mode=False):
        super().__init__(debug_mode=debug_mode, source_name='visir')
        self.base_url = "https://www.visir.is"

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
                    base_name=f"debug_visir_{self.debug_article_count}"
                )
                self.debug_article_count += 1

            # Parse with html.parser and handle HTML entities
            soup = BeautifulSoup(response.text, 'html.parser')
            self.logger.debug("Created BeautifulSoup object")

            # Find the main content container
            main_content = soup.find('div', class_='main-content')
            if not main_content:
                self.logger.debug("No main-content div found")
                return None

            # Extract article text
            self.logger.debug("Extracting article text")
            paragraphs = []

            # First get the summary paragraph from article-single__content
            summary_content = main_content.find(
                'div', class_='article-single__content')
            if summary_content:
                self.logger.debug("Found summary content")
                summary_p = summary_content.find('p')
                if summary_p:
                    text = summary_p.decode_contents().strip()
                    if text:
                        paragraphs.append(text)
                        self.logger.debug(
                            "Added summary paragraph: %s...", text[:50])

            # Then get the main article content
            article_content = main_content.find('article')
            if article_content:
                self.logger.debug("Found article content")
                # Find the article body div
                article_body = article_content.find(
                    'div', attrs={'itemprop': 'articleBody'})
                if article_body:
                    # Get all paragraphs, excluding those in ads
                    for p in article_body.find_all('p'):
                        # Only skip if the paragraph is directly inside an ad container
                        parent = p.find_parent('div', class_=lambda x: x and (
                            'adwrap' in x.lower() or 'placement' in x.lower()))
                        if parent:
                            self.logger.debug(
                                "Skipping p tag in ad container: %s...", p.text[:50])
                            continue
                        # Convert HTML entities to proper characters
                        text = p.decode_contents().strip()
                        if text:  # Only include non-empty paragraphs
                            paragraphs.append(text)
                            self.logger.debug(
                                "Added paragraph: %s...", text[:50])
                else:
                    self.logger.debug("No article body found")
            else:
                self.logger.debug("No article content found")

            article_text = "\n".join(paragraphs)
            self.logger.debug(
                "Final text length: %d characters", len(article_text))

            return article_text if article_text else None

        except Exception as e:
            self.logger.error(
                "Error fetching article content from %s: %s", url, str(e))
            return None
