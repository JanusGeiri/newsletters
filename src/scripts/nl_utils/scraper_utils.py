"""
Utility functions for news scraping operations.
"""
import os
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import json
from .logger_config import get_logger, get_module_name

# Get logger
logger = get_logger(get_module_name(__name__))


def save_debug_html(html_content: str, url: str, debug_dir: str) -> Optional[Path]:
    """Save raw HTML content for debugging purposes.

    Args:
        html_content (str): The HTML content to save
        url (str): The URL the HTML was fetched from
        debug_dir (str): Directory to save debug files in

    Returns:
        Optional[Path]: Path to the saved file if successful, None otherwise
    """
    try:
        # Create debug directory if it doesn't exist
        os.makedirs(debug_dir, exist_ok=True)

        # Generate filename from URL
        filename = url.split('/')[-1] + '.html'
        debug_file = Path(debug_dir) / filename

        # Save the HTML content
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.debug("Saved debug HTML to: %s", debug_file)
        return debug_file

    except Exception as e:
        logger.error("Error saving debug HTML: %s", str(e))
        return None


def save_combined_articles(articles: List[Dict], date: datetime, output_dir: str) -> Optional[Path]:
    """Save combined articles from all sources to a JSON file.

    Args:
        articles (List[Dict]): List of article dictionaries to save
        date (datetime): Date to use in the filename
        output_dir (str): Directory to save the file in

    Returns:
        Optional[Path]: Path to the saved file if successful, None otherwise
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Generate filename with date
        date_str = date.strftime("%Y-%m-%d")
        output_file = Path(output_dir) / f"news_articles_{date_str}.json"

        # Save articles to JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)

        logger.info("Saved %d articles to: %s", len(articles), output_file)
        return output_file

    except Exception as e:
        logger.error("Error saving combined articles: %s", str(e))
        return None


def ensure_output_dirs(output_dir: str, debug_dir: Optional[str] = None) -> None:
    """Ensure output directories exist.

    Args:
        output_dir (str): Main output directory for articles
        debug_dir (Optional[str]): Debug directory for HTML files
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        if debug_dir:
            os.makedirs(debug_dir, exist_ok=True)
    except Exception as e:
        logger.error("Error creating output directories: %s", str(e))
        raise
