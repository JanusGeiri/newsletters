"""
Master scraper class for orchestrating news scraping from multiple sources.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
import json
from nl_utils.logger_config import get_logger
from nl_utils import save_combined_articles
from .scrapers import VisirScraper, MblScraper, VbScraper, RUVScraper


class MasterScraper:
    """Class for orchestrating news scraping from multiple sources."""

    def __init__(self, debug_mode: bool = False):
        """Initialize the master scraper.

        Args:
            debug_mode: Whether to enable debug mode for scrapers
        """
        self.logger = get_logger('master_scraper')
        self.debug_mode = debug_mode
        self.scrapers = {
            'visir': VisirScraper(debug_mode=debug_mode),
            'mbl': MblScraper(debug_mode=debug_mode),
            'vb': VbScraper(debug_mode=debug_mode),
            'ruv': RUVScraper(debug_mode=debug_mode)
        }

    def get_available_sources(self) -> List[str]:
        """Get list of available news sources.

        Returns:
            List[str]: List of available source names
        """
        return list(self.scrapers.keys())

    def scrape_source(self, source_name: str, date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Scrape articles from a specific source.

        Args:
            source_name: Name of the source to scrape
            date: Date to scrape articles for. If None, uses current date

        Returns:
            List[Dict[str, Any]]: List of scraped articles

        Raises:
            ValueError: If source_name is not valid
        """
        if source_name not in self.scrapers:
            raise ValueError(
                f"Invalid source name: {source_name}. Available sources: {self.get_available_sources()}")

        if date is None:
            date = datetime.now()

        try:
            self.logger.info("Processing articles from %s", source_name)
            articles = self.scrapers[source_name].process_articles(date)
            if articles:
                self.logger.info(
                    "Successfully processed %d articles from %s", len(articles), source_name)
            else:
                self.logger.warning("No articles found for %s", source_name)
            return articles
        except Exception as e:
            self.logger.error("Error processing %s: %s", source_name, str(e))
            return []

    def scrape_all_sources(self, date: Optional[datetime] = None, sources: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Scrape articles from all or specified sources.

        Args:
            date: Date to scrape articles for. If None, uses current date
            sources: List of sources to scrape. If None, scrapes all sources

        Returns:
            List[Dict[str, Any]]: List of all scraped articles
        """
        if date is None:
            date = datetime.now()

        if sources is None:
            sources = self.get_available_sources()

        all_articles = []
        for source_name in sources:
            articles = self.scrape_source(source_name, date)
            all_articles.extend(articles)

        return all_articles

    def save_articles(self, articles: List[Dict[str, Any]], date: Optional[datetime] = None, output_dir: Optional[str] = None) -> Optional[Path]:
        """Save scraped articles to a file.

        Args:
            articles: List of articles to save
            date: Date to use in filename. If None, uses current date
            output_dir: Directory to save articles in. If None, uses default directory

        Returns:
            Optional[Path]: Path to saved file if successful, None otherwise
        """
        if not articles:
            self.logger.warning("No articles to save")
            return None

        if date is None:
            date = datetime.now()

        if output_dir is None:
            output_dir = "src/outputs/news/json"

        try:
            output_path = save_combined_articles(articles, date, output_dir)
            self.logger.info(
                "Successfully saved %d articles to %s", len(articles), output_path)
            return output_path
        except Exception as e:
            self.logger.error("Error saving articles: %s", str(e))
            return None

    def run_scraper(
        self,
        date: Optional[datetime] = None,
        sources: Optional[List[str]] = None,
        output_dir: Optional[str] = None,
        ignore: bool = False
    ) -> Optional[Path]:
        """Run the complete scraping process.

        Args:
            date: Date to scrape articles for. If None, uses current date
            sources: List of sources to scrape. If None, scrapes all sources
            output_dir: Directory to save articles in. If None, uses default directory
            ignore: If True, skip scraping and return a dummy path

        Returns:
            Optional[Path]: Path to saved file if successful, None otherwise
        """
        if ignore:
            self.logger.info("Ignoring scraping operation")
            return Path('src/outputs/news/json/dummy.json')

        try:
            self.logger.info("Starting news scraper")
            if date is None:
                date = datetime.now()
            self.logger.info("Scraping news for date: %s",
                             date.strftime("%Y-%m-%d"))

            # Scrape articles from all sources
            articles = self.scrape_all_sources(date, sources)

            # Save articles
            if articles:
                return self.save_articles(articles, date, output_dir)
            else:
                self.logger.warning("No articles were processed")
                return None

        except Exception as e:
            self.logger.error("Error in scraping process: %s", str(e))
            return None
