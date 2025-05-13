import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import time
import re
from tqdm import tqdm
import os
from abc import ABC, abstractmethod
import feedparser
from logger_config import get_logger

# Get logger
logger = get_logger('news_scraper')


class RSSFeedHandler:
    """Handles fetching and processing of RSS feeds from various news sources"""

    def __init__(self):
        self.feed_links = {
            'visir': [
                'https://www.visir.is/rss/allt'
            ],
            'mbl': [
                "https://www.mbl.is/feeds/fp/",
                "https://www.mbl.is/feeds/innlent/",
                "https://www.mbl.is/feeds/erlent/",
                "https://www.mbl.is/feeds/togt/",
                "https://www.mbl.is/feeds/vidskipti/",
                "https://www.mbl.is/feeds/200milur/",
                "https://www.mbl.is/feeds/sport/",
                "https://www.mbl.is/feeds/fotbolti/",
                "https://www.mbl.is/feeds/enski/",
                "https://www.mbl.is/feeds/golf/",
                "https://www.mbl.is/feeds/handbolti/",
                "https://www.mbl.is/feeds/korfubolti/",
                "https://www.mbl.is/feeds/pepsideild/",
                "https://www.mbl.is/feeds/formula/",
                "https://www.mbl.is/feeds/rafithrottir/",
                "https://www.mbl.is/feeds/folk/",
                "https://www.mbl.is/feeds/verold/",
                "https://www.mbl.is/feeds/matur/",
                "https://www.mbl.is/feeds/ferdalog/",
                "https://www.mbl.is/feeds/smartland/",
                "https://www.mbl.is/feeds/stars/",
                "https://www.mbl.is/feeds/tiska/",
                "https://www.mbl.is/feeds/heimili/",
                "https://www.mbl.is/feeds/utlit/",
                "https://www.mbl.is/feeds/heilsa/",
                "https://www.mbl.is/feeds/frami/",
                "https://www.mbl.is/feeds/samkvaemislifid/",
                "https://www.mbl.is/feeds/fjolskyldan/",
                "https://www.mbl.is/feeds/k100/",
                "https://www.mbl.is/feeds/blog/"
            ],
            'vb': [
                'https://www.vb.is/rss'
            ],
            'ruv': [
                'https://www.ruv.is/rss/frettir',
                'https://www.ruv.is/rss/innlent',
                'https://www.ruv.is/rss/erlent',
                'https://www.ruv.is/rss/ithrottir',
                'https://www.ruv.is/rss/menning-og-daegurmal'
            ]
        }

    def get_articles(self, source=None):
        """Get articles from RSS feeds

        Args:
            source: Optional source name to filter feeds by (e.g., 'visir', 'mbl')

        Returns:
            List of article dictionaries
        """
        articles = []
        processed_urls = set()  # Keep track of processed URLs to avoid duplicates

        # If source is specified, only process feeds for that source
        sources_to_process = [source] if source else self.feed_links.keys()

        for source_name in sources_to_process:
            if source_name not in self.feed_links:
                print(f"Warning: Unknown source {source_name}")
                continue

            for feed_url in self.feed_links[source_name]:
                try:
                    feed = feedparser.parse(feed_url)
                    for entry in feed.entries:
                        # Skip if we've already processed this URL
                        if entry.link in processed_urls:
                            continue

                        # Use feedparser's parsed date if available, otherwise use published
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            date_obj = datetime(*entry.published_parsed[:6])
                            formatted_date = date_obj.strftime(
                                "%Y-%m-%d %H:%M:%S")
                        else:
                            formatted_date = None

                        article = {
                            "article_source": source_name,
                            "article_title": entry.title,
                            "article_date": formatted_date,
                            "article_description": entry.description,
                            "article_url": entry.link,
                        }
                        articles.append(article)
                        # Add URL to processed set
                        processed_urls.add(entry.link)
                except Exception as e:
                    print(f"Error fetching feed {feed_url}: {str(e)}")
        return articles


class NewsScraper(ABC):
    def __init__(self, debug_mode=False, source_name=None):
        self.debug_mode = debug_mode
        self.debug_article_count = 0
        self.output_dir = "src/outputs/news/json"
        self.debug_dir = "debug"
        # Name of the news source (e.g., 'visir', 'mbl')
        self.source_name = source_name
        self.rss_handler = RSSFeedHandler()
        self.logger = get_logger(f'news_scraper_{source_name}')

    def ensure_output_dir(self):
        """Ensure the output directories exist"""
        os.makedirs(self.output_dir, exist_ok=True)
        if self.debug_mode:
            os.makedirs(self.debug_dir, exist_ok=True)

    def debug_print(self, message):
        """Print debug message only if debug mode is enabled"""
        if self.debug_mode:
            print(message)
            self.logger.debug(message)

    @abstractmethod
    def get_article_content(self, url):
        """Get the content of a single article. Must be implemented by each news source."""
        pass

    def format_date(self, date_str):
        """Format date string to YYYY-MM-DD format

        Args:
            date_str: Date string in various formats (e.g., "Sat, 10 May 2025 22:30:06 Z", "2024-05-10T12:00:00")

        Returns:
            Formatted date string in YYYY-MM-DD format
        """
        try:
            # Try parsing RSS feed format first (e.g., "Sat, 10 May 2025 22:30:06 Z")
            date_obj = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %Z")
        except ValueError:
            try:
                # Try parsing ISO format
                date_obj = datetime.fromisoformat(date_str)
            except ValueError:
                try:
                    # Try parsing just the date part
                    date_obj = datetime.strptime(date_str[:10], "%Y-%m-%d")
                except ValueError:
                    self.debug_print(
                        f"[DEBUG] Could not parse date: {date_str}")
                    return None

        return date_obj.strftime("%Y-%m-%d")

    def process_articles(self, target_date):
        """Process articles from RSS feeds for the specified date

        Args:
            target_date: Date to filter articles by
        """
        # Get articles from RSS feeds
        rss_data = self.rss_handler.get_articles(source=self.source_name)
        self.logger.info(
            f"Retrieved {len(rss_data)} articles from {self.source_name} RSS feed")

        # Process the articles
        return self.process_rss_articles(rss_data, target_date)

    def process_rss_articles(self, rss_data, target_date):
        """Process articles from RSS feed data

        Args:
            rss_data: List of dictionaries containing RSS feed data
            target_date: Date to filter articles by
        """
        # Ensure output directories exist
        self.ensure_output_dir()

        processed_articles = []
        processed_urls = set()

        # Filter articles by source and date
        target_date_str = target_date.strftime("%Y-%m-%d")
        filtered_articles = [
            article for article in rss_data
            if article['article_source'] == self.source_name and
            self.format_date(article['article_date']) == target_date_str
        ]

        self.logger.info(
            f"Found {len(filtered_articles)} articles from {self.source_name} for {target_date_str}")

        if self.debug_mode:
            self.debug_print(
                f"\n[DEBUG] Found {len(filtered_articles)} articles from {self.source_name} for {target_date_str}")
            self.debug_print("[DEBUG] Filtered articles:")
            for article in filtered_articles:
                self.debug_print(
                    f"  - {article['article_title']} ({article['article_date']})")

        for i, article in enumerate(filtered_articles):
            if i % 10 == 0:
                self.logger.info(
                    f"Processing article {i+1} of {len(filtered_articles)} from {self.source_name}")
            url = article['article_url']

            # Skip if we've already processed this URL
            if url in processed_urls:
                self.logger.debug(f"Skipping duplicate article: {url}")
                continue

            # Get article content
            self.logger.debug(
                f"Fetching content for article: {article['article_title']}")
            content = self.get_article_content(url)
            if content:
                # Combine RSS data with scraped content
                article_data = {
                    "article_source": article['article_source'],
                    "article_title": article['article_title'],
                    "article_url": url,
                    "article_date": article['article_date'],
                    "article_description": article['article_description'],
                    "article_text": content
                }
                processed_articles.append(article_data)
                processed_urls.add(url)
                self.logger.debug(
                    f"Successfully processed article: {article['article_title']}")
            else:
                self.logger.warning(
                    f"Failed to get content for article: {article['article_title']}")

        self.logger.info(
            f"Completed processing {len(processed_articles)} articles from {self.source_name}")
        return processed_articles


class VisirScraper(NewsScraper):
    def __init__(self, debug_mode=False):
        super().__init__(debug_mode=debug_mode, source_name='visir')
        self.base_url = "https://www.visir.is"

    def get_article_content(self, url):
        """Get the content of a single article"""
        try:
            self.debug_print(
                f"\n[DEBUG] Starting to fetch article from: {url}")

            # Fetch the page
            response = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            response.raise_for_status()

            # Save raw HTML for debugging
            if self.debug_mode:
                filename = url.split('/')[-1] + '.html'
                debug_file = os.path.join(self.debug_dir, filename)
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                self.debug_print(f"[DEBUG] Saved raw HTML to: {debug_file}")

            # Parse with html.parser and handle HTML entities
            soup = BeautifulSoup(response.text, 'html.parser')
            self.debug_print("[DEBUG] Created BeautifulSoup object")

            # Find the main content container
            main_content = soup.find('div', class_='main-content')
            if not main_content:
                self.debug_print("[DEBUG] No main-content div found")
                return None

            # Extract article text
            self.debug_print("\n[DEBUG] Extracting article text")
            paragraphs = []

            # First get the summary paragraph from article-single__content
            summary_content = main_content.find(
                'div', class_='article-single__content')
            if summary_content:
                self.debug_print("[DEBUG] Found summary content")
                summary_p = summary_content.find('p')
                if summary_p:
                    text = summary_p.decode_contents().strip()
                    if text:
                        paragraphs.append(text)
                        self.debug_print(
                            f"[DEBUG] Added summary paragraph: {text[:50]}...")

            # Then get the main article content
            article_content = main_content.find('article')
            if article_content:
                self.debug_print("[DEBUG] Found article content")
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
                            self.debug_print(
                                f"[DEBUG] Skipping p tag in ad container: {p.text[:50]}...")
                            continue
                        # Convert HTML entities to proper characters
                        text = p.decode_contents().strip()
                        if text:  # Only include non-empty paragraphs
                            paragraphs.append(text)
                            self.debug_print(
                                f"[DEBUG] Added paragraph: {text[:50]}...")
                else:
                    self.debug_print("[DEBUG] No article body found")
            else:
                self.debug_print("[DEBUG] No article content found")

            article_text = "\n".join(paragraphs)
            self.debug_print(
                f"[DEBUG] Final text length: {len(article_text)} characters")

            return article_text if article_text else None

        except Exception as e:
            print(f"Error fetching article content from {url}: {str(e)}")
            return None


class MblScraper(NewsScraper):
    def __init__(self, debug_mode=False):
        super().__init__(debug_mode=debug_mode, source_name='mbl')
        self.base_url = "https://www.mbl.is"

    def get_article_content(self, url):
        """Get the content of a single article"""
        try:
            self.debug_print(
                f"\n[DEBUG] Starting to fetch article from: {url}")

            # Fetch the page
            response = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            response.raise_for_status()

            # Save raw HTML for debugging
            if self.debug_mode:
                filename = url.split('/')[-1] + '.html'
                debug_file = os.path.join(self.debug_dir, filename)
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                self.debug_print(f"[DEBUG] Saved raw HTML to: {debug_file}")

            # Parse with html.parser and handle HTML entities
            soup = BeautifulSoup(response.text, 'html.parser')
            self.debug_print("[DEBUG] Created BeautifulSoup object")

            # Find the main content container
            main_content = soup.find('div', class_='main-layout')
            if not main_content:
                self.debug_print("[DEBUG] No main-layout div found")
                return None

            # Extract article text
            self.debug_print("\n[DEBUG] Extracting article text")
            paragraphs = []

            # First check for restricted content (hidden content that's actually visible)
            restricted_content = main_content.find(
                'div', class_='mbl-newsitem-restricted')
            if restricted_content:
                self.debug_print("[DEBUG] Found restricted content")
                for p in restricted_content.find_all('p'):
                    text = p.decode_contents().strip()
                    if text:
                        paragraphs.append(text)
                        self.debug_print(
                            f"[DEBUG] Added restricted paragraph: {text[:50]}...")

            # Then get the main article content
            # Look for paragraphs in the main content, excluding those in ads
            for p in main_content.find_all('p'):
                # Skip if the paragraph is in an ad container
                parent = p.find_parent('div', class_=lambda x: x and (
                    'augl' in x.lower() or 'ad' in x.lower()))
                if parent:
                    self.debug_print(
                        f"[DEBUG] Skipping p tag in ad container: {p.text[:50]}...")
                    continue

                # Skip if the paragraph is in restricted content (we already processed it)
                if p.find_parent('div', class_='mbl-newsitem-restricted'):
                    continue

                # Convert HTML entities to proper characters
                text = p.decode_contents().strip()
                if text:  # Only include non-empty paragraphs
                    paragraphs.append(text)
                    self.debug_print(
                        f"[DEBUG] Added paragraph: {text[:50]}...")

            article_text = "\n".join(paragraphs)
            self.debug_print(
                f"[DEBUG] Final text length: {len(article_text)} characters")

            return article_text if article_text else None

        except Exception as e:
            print(f"Error fetching article content from {url}: {str(e)}")
            return None


class VbScraper(NewsScraper):
    def __init__(self, debug_mode=False):
        super().__init__(debug_mode=debug_mode, source_name='vb')
        self.base_url = "https://www.vb.is"

    def get_article_content(self, url):
        """Get the content of a single article"""
        try:
            self.debug_print(
                f"\n[DEBUG] Starting to fetch article from: {url}")

            # Fetch the page
            response = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            response.raise_for_status()

            # Save raw HTML for debugging
            if self.debug_mode:
                filename = url.split('/')[-1] + '.html'
                debug_file = os.path.join(self.debug_dir, filename)
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                self.debug_print(f"[DEBUG] Saved raw HTML to: {debug_file}")

            # Parse with html.parser and handle HTML entities
            soup = BeautifulSoup(response.text, 'html.parser')
            self.debug_print("[DEBUG] Created BeautifulSoup object")

            # Extract article text
            self.debug_print("\n[DEBUG] Extracting article text")
            paragraphs = []

            # Find all paragraph blocks
            paragraph_blocks = soup.find_all('div', class_='paragraph-block')
            if not paragraph_blocks:
                self.debug_print("[DEBUG] No paragraph blocks found")
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
                    self.debug_print(
                        f"[DEBUG] Skipping paragraph block in ad container: {parent.get('class', [])}")
                    continue

                # Get all paragraphs in the block
                for p in block.find_all('p'):
                    # Convert HTML entities to proper characters
                    text = p.decode_contents().strip()
                    if text:  # Only include non-empty paragraphs
                        paragraphs.append(text)
                        self.debug_print(
                            f"[DEBUG] Added paragraph: {text[:50]}...")

            article_text = "\n".join(paragraphs)
            self.debug_print(
                f"[DEBUG] Final text length: {len(article_text)} characters")

            return article_text if article_text else None

        except Exception as e:
            print(f"Error fetching article content from {url}: {str(e)}")
            return None


class RUVScraper(NewsScraper):
    def __init__(self, debug_mode=False):
        super().__init__(debug_mode=debug_mode, source_name='ruv')
        self.base_url = "https://www.ruv.is"

    def get_article_content(self, url):
        """Get the content of a single article from RUV"""
        try:
            self.debug_print(
                f"\n[DEBUG] Starting to fetch article from: {url}")

            # Fetch the page
            response = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            response.raise_for_status()

            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find the JSON data in the script tag
            script_tag = soup.find('script', {'id': '__NEXT_DATA__'})
            if not script_tag:
                self.debug_print(
                    "[DEBUG] Could not find __NEXT_DATA__ script tag")
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
                self.debug_print(
                    f"[DEBUG] Error extracting article text: {str(e)}")
                return None

        except Exception as e:
            self.debug_print(f"[DEBUG] Error fetching article: {str(e)}")
            return None


def main():
    # Enable debug mode by setting to True
    debug_mode = False
    visir_scraper = VisirScraper(debug_mode=debug_mode)
    mbl_scraper = MblScraper(debug_mode=debug_mode)
    vb_scraper = VbScraper(debug_mode=debug_mode)
    ruv_scraper = RUVScraper(debug_mode=debug_mode)

    # Get today's date
    today = datetime.now().date()
    today = datetime(2025, 5, 13).date()

    # Process articles from all sources

    visir_articles = visir_scraper.process_articles(today)
    mbl_articles = mbl_scraper.process_articles(today)
    vb_articles = vb_scraper.process_articles(today)
    ruv_articles = ruv_scraper.process_articles(today)

    # Combine articles from all sources
    all_articles = visir_articles + mbl_articles + vb_articles + ruv_articles
    # Save to JSON file in the output directory
    output_file = os.path.join(
        "src", "outputs", "news", "json", f"news_articles_{today}.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_articles, f, ensure_ascii=False, indent=2)

    print(
        f"\nProcessed {len(visir_articles)} Visir articles, {len(mbl_articles)} MBL articles, {len(vb_articles)} VB articles, and {len(ruv_articles)} RUV articles")
    print(f"Saved {len(all_articles)} total articles to {output_file}")


if __name__ == "__main__":
    main()
