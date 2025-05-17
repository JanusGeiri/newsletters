#!/usr/bin/env python3
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from bs4 import BeautifulSoup
from dotenv import load_dotenv

from nl_utils.logger_config import get_logger
from nl_utils.file_handler import FileHandler, FileType

# Load environment variables
load_dotenv()

# Get logger
logger = get_logger('update_index')


class NewsletterIndexUpdater:
    """Class to handle newsletter index updates."""

    def __init__(self, index_path: str = 'index.html'):
        """Initialize the NewsletterIndexUpdater.

        Args:
            index_path (str): Path to index.html file
        """
        self.file_handler = FileHandler()
        self.index_path = Path(index_path)
        self.logger = logger

    def get_newsletter_files(self) -> List[Path]:
        """Get all newsletter files from the formatted newsletters directory.

        Returns:
            List[Path]: List of newsletter file paths sorted by date (newest first)
        """
        try:
            directory = Path(
                self.file_handler.DIRECTORIES[FileType.FORMATTED_NEWSLETTER])
            if not directory.exists():
                self.logger.warning(
                    "Newsletter directory not found: %s", directory)
                return []

            # Get all HTML files and sort by date (newest first)
            files = list(directory.glob('newsletter_formatted_*.html'))
            # Sort by filename date instead of modification time for more reliable ordering
            files.sort(key=lambda x: self._extract_date_from_filename(x)
                       or '', reverse=True)
            self.logger.info("Found %d newsletter files", len(files))
            return files
        except Exception as e:
            self.logger.error("Error getting newsletter files: %s", str(e))
            return []

    @staticmethod
    def _extract_date_from_filename(filename: Path) -> Optional[str]:
        """Extract date from filename in format YYYY-MM-DD.

        Args:
            filename (Path): Path object of the filename

        Returns:
            Optional[str]: Extracted date string or None if not found
        """
        match = re.search(
            r'newsletter_formatted_(\d{4}-\d{2}-\d{2})\.html', filename.name)
        return match.group(1) if match else None

    def _format_newsletter_title(self, date_str: str) -> str:
        """Format newsletter title with news date and send date.

        Args:
            date_str (str): Date string in YYYY-MM-DD format

        Returns:
            str: Formatted title string
        """
        news_date = datetime.strptime(date_str, '%Y-%m-%d')
        send_date = news_date + timedelta(days=1)
        return f'Fréttabréf ({date_str}) - sent {send_date.strftime("%Y-%m-%d")}'

    def _update_latest_section(self, soup: BeautifulSoup, latest_file: Path) -> None:
        """Update the latest newsletter section in the index.

        Args:
            soup (BeautifulSoup): BeautifulSoup object of the index
            latest_file (Path): Path to the latest newsletter file
        """
        latest_section = soup.find('div', class_='latest-newsletter')
        if not latest_section:
            return

        latest_date = self._extract_date_from_filename(latest_file)
        if not latest_date:
            return

        latest_link = latest_section.find('a')
        if not latest_link:
            return

        latest_link[
            'href'] = f'/newsletters/src/outputs/newsletters/formatted/{latest_file.name}'
        latest_title = latest_link.find('h3')
        if latest_title:
            latest_title.string = self._format_newsletter_title(latest_date)
            self.logger.info(
                "Updated latest newsletter link for date: %s", latest_date)

    def _update_newsletter_list(self, soup: BeautifulSoup, newsletter_files: List[Path]) -> None:
        """Update the newsletter list section in the index.

        Args:
            soup (BeautifulSoup): BeautifulSoup object of the index
            newsletter_files (List[Path]): List of newsletter file paths
        """
        newsletter_list = soup.find('div', class_='newsletter-list')
        if not newsletter_list:
            return

        # Clear existing links
        newsletter_list.clear()

        # Add new links
        for file in newsletter_files:
            date = self._extract_date_from_filename(file)
            if not date:
                continue

            link = soup.new_tag('a',
                                href=f'/newsletters/src/outputs/newsletters/formatted/{file.name}',
                                attrs={'class': 'newsletter-link'})
            card = soup.new_tag('div', attrs={'class': 'newsletter-card'})
            title = soup.new_tag('h3')
            title.string = self._format_newsletter_title(date)
            card.append(title)
            link.append(card)
            newsletter_list.append(link)

        self.logger.info(
            "Updated newsletter list with %d entries", len(newsletter_files))

    def update_index_html(self) -> None:
        """Update index.html with latest newsletter links."""
        if not self.index_path.exists():
            self.logger.error("Index file not found: %s", self.index_path)
            return

        try:
            with open(self.index_path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')

            # Get newsletter files
            newsletter_files = self.get_newsletter_files()
            if not newsletter_files:
                self.logger.warning("No newsletter files found!")
                return

            # Update sections
            self._update_latest_section(soup, newsletter_files[0])
            self._update_newsletter_list(soup, newsletter_files)

            # Write updated index.html
            with open(self.index_path, 'w', encoding='utf-8') as f:
                f.write(str(soup))
            self.logger.info("Successfully wrote updated index.html")

        except Exception as e:
            self.logger.error("Error updating index.html: %s", str(e))
            raise

    def update_index(self, ignore: bool = False) -> None:
        """Update the index of newsletters.

        Args:
            ignore (bool): If True, skip updating and return immediately
        """
        if ignore:
            self.logger.info("Ignoring index update operation")
            return

        try:
            self.logger.info("Starting index update...")
            self.update_index_html()
            self.logger.info("Index update completed successfully")

        except Exception as e:
            self.logger.error("Error updating index: %s", str(e))
            raise


def update_index(ignore: bool = False) -> None:
    """Legacy function to maintain backward compatibility.

    Args:
        ignore (bool): If True, skip updating and return immediately
    """
    updater = NewsletterIndexUpdater()
    updater.update_index(ignore=ignore)


if __name__ == "__main__":
    update_index()
