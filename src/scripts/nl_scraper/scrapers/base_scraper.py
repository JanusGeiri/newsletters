"""
Base news scraper class that defines the interface for all news scrapers.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

from nl_utils.logger_config import get_logger
from nl_utils.file_handler import FileHandler
from ..rss_handler import RSSFeedHandler


class NewsScraper(ABC):
    """Base class for news scrapers that defines the interface and common functionality."""

    def __init__(self, debug_mode: bool = False, source_name: Optional[str] = None) -> None:
        """Initialize the news scraper.

        Args:
            debug_mode (bool): Whether to run in debug mode
            source_name (Optional[str]): Name of the news source (e.g., 'visir', 'mbl')
        """
        self.debug_mode = debug_mode
        self.debug_article_count = 0
        self.file_handler = FileHandler()
        self.debug_dir = Path("debug")
        self.source_name = source_name
        self.rss_handler = RSSFeedHandler()
        self.logger = get_logger(f'news_scraper_{source_name}')

    def ensure_output_dir(self) -> None:
        """Ensure the output directories exist."""
        if self.debug_mode:
            self.debug_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def get_article_content(self, url: str) -> Optional[str]:
        """Get the content of a single article. Must be implemented by each news source.

        Args:
            url (str): URL of the article to scrape

        Returns:
            Optional[str]: The article content if successful, None otherwise
        """

    def format_date(self, date_str: str) -> Optional[str]:
        """Format date string to YYYY-MM-DD format.

        Args:
            date_str (str): Date string in various formats (e.g., "Sat, 10 May 2025 22:30:06 Z", "2024-05-10T12:00:00")

        Returns:
            Optional[str]: Formatted date string in YYYY-MM-DD format, or None if parsing fails
        """
        date_formats = [
            ("%a, %d %b %Y %H:%M:%S %Z", "RSS feed format"),
            ("%Y-%m-%dT%H:%M:%S", "ISO format"),
            ("%Y-%m-%d %H:%M:%S", "ISO format"),
            ("%Y-%m-%d", "Date only format")
        ]

        for date_format, _ in date_formats:
            try:
                date_obj = datetime.strptime(date_str, date_format)
                return date_obj.strftime("%Y-%m-%d")
            except ValueError:
                continue

        self.logger.info("Could not parse date: %s", date_str)
        return None

    def process_articles(self, target_date: datetime) -> List[Dict]:
        """Process articles from RSS feeds for the specified date.

        Args:
            target_date (datetime): Date to filter articles by

        Returns:
            List[Dict]: List of processed articles
        """
        # Get articles from RSS feeds
        rss_data = self.rss_handler.get_articles(source=self.source_name)
        self.logger.info(
            "Retrieved %d articles from %s RSS feed",
            len(rss_data),
            self.source_name
        )

        # Process the articles
        return self.process_rss_articles(rss_data, target_date)

    def _filter_articles_by_date(
        self,
        articles: List[Dict],
        target_date: datetime
    ) -> List[Dict]:
        """Filter articles by source and date.

        Args:
            articles (List[Dict]): List of articles to filter
            target_date (datetime): Target date to filter by

        Returns:
            List[Dict]: Filtered list of articles
        """
        target_date_str = target_date.strftime("%Y-%m-%d")
        filtered_articles = [
            article for article in articles
            if (article['article_source'] == self.source_name and
                self.format_date(article['article_date']) == target_date_str)
        ]

        self.logger.info(
            "Found %d articles from %s for %s",
            len(filtered_articles),
            self.source_name,
            target_date_str
        )

        if self.debug_mode:
            self._log_filtered_articles(filtered_articles)

        return filtered_articles

    def _log_filtered_articles(self, articles: List[Dict]) -> None:
        """Log filtered articles in debug mode.

        Args:
            articles (List[Dict]): List of filtered articles to log
        """
        self.logger.debug(
            "Found %d articles from %s",
            len(articles),
            self.source_name
        )
        self.logger.debug("Filtered articles:")
        for article in articles:
            self.logger.debug(
                "  - %s (%s)",
                article['article_title'],
                article['article_date']
            )

    def _process_single_article(
        self,
        article: Dict,
        processed_urls: Set[str]
    ) -> Optional[Dict]:
        """Process a single article.

        Args:
            article (Dict): Article data from RSS feed
            processed_urls (Set[str]): Set of already processed URLs

        Returns:
            Optional[Dict]: Processed article data if successful, None otherwise
        """
        url = article['article_url']

        # Skip if we've already processed this URL
        if url in processed_urls:
            self.logger.debug("Skipping duplicate article: %s", url)
            return None

        # Get article content
        self.logger.debug(
            "Fetching content for article: %s from %s",
            article['article_title'],
            url
        )
        content = self.get_article_content(url)
        if not content:
            self.logger.warning(
                "Failed to get content for article: %s from %s",
                article['article_title'],
                url
            )
            return None

        # Combine RSS data with scraped content
        article_data = {
            "article_source": article['article_source'],
            "article_title": article['article_title'],
            "article_url": url,
            "article_date": article['article_date'],
            "article_description": article['article_description'],
            "article_text": content
        }
        processed_urls.add(url)
        self.logger.debug(
            "Successfully processed article: %s from %s",
            article['article_title'],
            url
        )
        return article_data

    def process_rss_articles(
        self,
        rss_data: List[Dict],
        target_date: datetime
    ) -> List[Dict]:
        """Process articles from RSS feed data.

        Args:
            rss_data (List[Dict]): List of dictionaries containing RSS feed data
            target_date (datetime): Date to filter articles by

        Returns:
            List[Dict]: List of processed articles
        """
        # Ensure output directories exist
        self.ensure_output_dir()

        processed_articles = []
        processed_urls = set()

        # Filter articles by source and date
        filtered_articles = self._filter_articles_by_date(
            rss_data, target_date)

        # Process each article
        for i, article in enumerate(filtered_articles):
            if i % 10 == 0:
                self.logger.info(
                    "Processing article %d of %d from %s",
                    i + 1,
                    len(filtered_articles),
                    self.source_name
                )

            processed_article = self._process_single_article(
                article, processed_urls)
            if processed_article:
                processed_articles.append(processed_article)

        self.logger.info(
            "Completed processing %d articles from %s",
            len(processed_articles),
            self.source_name
        )
        return processed_articles
