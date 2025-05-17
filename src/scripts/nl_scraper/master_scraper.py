"""
Master scraper class for orchestrating news scraping from multiple sources.
"""
import hashlib
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
from nl_utils.logger_config import get_logger, get_module_name
from nl_utils.file_handler import FileHandler, FileType
from nl_article_processor.text_processor import TextProcessor
from .scrapers import VisirScraper, MblScraper, VbScraper, RUVScraper


class MasterScraper:
    """Class for orchestrating news scraping from multiple sources."""

    def __init__(self, debug_mode: bool = False):
        """Initialize the master scraper.

        Args:
            debug_mode: Whether to enable debug mode for scrapers
        """
        self.logger = get_logger(get_module_name(__name__))
        self.debug_mode = debug_mode
        self.file_handler = FileHandler()
        self.text_processor = TextProcessor(debug_mode=debug_mode)
        self.scrapers = {
            'visir': VisirScraper(debug_mode=debug_mode),
            'mbl': MblScraper(debug_mode=debug_mode),
            'vb': VbScraper(debug_mode=debug_mode),
            'ruv': RUVScraper(debug_mode=debug_mode)
        }

    def generate_article_id(self, article: Dict[str, Any]) -> str:
        """Generate a unique article ID based on article content.

        Args:
            article: Article dictionary containing source, URL, and title

        Returns:
            str: Unique article ID in format 'source_hash'
        """
        try:
            # Create a unique string from article metadata
            unique_str = f"{article.get('article_source', 'unknown')}_{article.get('article_url', '')}_{article.get('article_title', '')}"

            # Generate MD5 hash
            hash_obj = hashlib.md5(unique_str.encode('utf-8'))
            # Use first 8 characters of hash
            hash_hex = hash_obj.hexdigest()[:32]

            # Create ID in format 'source_hash'
            source = article.get('article_source', 'unknown').lower()
            return f"{source}_{hash_hex}"

        except Exception as e:
            self.logger.error("Error generating article ID: %s", str(e))
            return f"unknown_{hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]}"

    def add_article_ids(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add unique article IDs to each article.

        Args:
            articles: List of articles to process

        Returns:
            List[Dict[str, Any]]: List of articles with added IDs
        """
        for article in articles:
            if 'article_id' not in article:
                article['article_id'] = self.generate_article_id(article)
        return articles

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
                # Add article IDs
                articles = self.add_article_ids(articles)
                self.logger.info(
                    "Successfully processed %d articles from %s", len(articles), source_name)
            else:
                self.logger.warning("No articles found for %s", source_name)
            return articles
        except Exception as e:
            self.logger.error("Error processing %s: %s", source_name, str(e))
            return []

    def process_article_text(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process article text and add lemmas to each article.

        Args:
            articles: List of articles to process

        Returns:
            List[Dict[str, Any]]: List of processed articles with cleaned text and lemmas
        """
        processed_articles = []
        for idx, article in enumerate(articles, 1):
            try:
                article_text = article.get('article_text', '')
                article_source = article.get('article_source', 'Unknown')
                article_id = article.get('article_id', f'article_{idx}')

                if not article_text:
                    self.logger.warning(
                        "Empty text for article %s from %s", article_id, article_source)
                    continue

                self.logger.info(
                    "Processing text for article %d/%d: %s from %s",
                    idx, len(articles), article_id, article_source)

                # Clean the article text
                cleaned_text = self.text_processor.clean_html_text(
                    article_text)
                article['article_text'] = cleaned_text

                # Extract lemmas
                lemmas = self.text_processor.extract_lemmas(
                    cleaned_text, article_source)
                # Changed from 'lemmas' to 'article_lemmas'
                article['article_lemmas'] = lemmas

                processed_articles.append(article)

            except Exception as e:
                self.logger.error(
                    "Error processing article %s from %s (url: %s): %s\nText that failed: %s",
                    article.get('article_id', f'article_{idx}'),
                    article.get('article_source', 'Unknown'),
                    article.get('article_url', 'No URL'),
                    str(e),
                    article.get('article_text', 'No text'))
                continue

        return processed_articles

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

    def save_articles(self, articles: List[Dict[str, Any]], date: Optional[datetime] = None) -> Optional[Path]:
        """Save scraped articles to a file.

        Args:
            articles: List of articles to save
            date: Date to use in filename. If None, uses current date

        Returns:
            Optional[Path]: Path to saved file if successful, None otherwise
        """
        if not articles:
            self.logger.warning("No articles to save")
            return None

        if date is None:
            date = datetime.now()

        try:
            date_str = date.strftime("%Y-%m-%d")
            output_path = self.file_handler.save_file(
                articles,
                FileType.ARTICLES,
                date_str=date_str,
                base_name="articles"
            )
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
        ignore: bool = False
    ) -> Optional[Path]:
        """Run the complete scraping process.

        Args:
            date: Date to scrape articles for. If None, uses current date
            sources: List of sources to scrape. If None, scrapes all sources
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
            if not articles:
                self.logger.warning("No articles were scraped")
                return None

            # Process article text and add lemmas
            self.logger.info("Processing article text and extracting lemmas")
            processed_articles = self.process_article_text(articles)
            if not processed_articles:
                self.logger.warning("No articles were processed")
                return None

            # Save processed articles
            return self.save_articles(processed_articles, date)

        except Exception as e:
            self.logger.error("Error in scraping process: %s", str(e))
            return None
