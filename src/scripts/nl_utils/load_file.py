"""
Standardized file loading utilities for the newsletter system.
"""
import json
from pathlib import Path
from typing import Union, Dict, List, Tuple, Optional
from datetime import datetime
from .logger_config import get_logger
import os
import re

logger = get_logger('file_utils')


def load_json_file(file_path: Union[str, Path]) -> Union[Dict, List]:
    """Load data from a JSON file with standardized error handling and logging.

    Args:
        file_path: Path to the JSON file

    Returns:
        Union[Dict, List]: The loaded JSON data

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
        ValueError: If data is not a dict or list
    """
    try:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, (dict, list)):
            raise ValueError(
                f"Invalid JSON content in {file_path}: expected dictionary or list, got {type(data)}")

        logger.info("Loaded JSON file from: %s", file_path)
        return data

    except Exception as e:
        logger.error("Error loading JSON file from %s: %s", file_path, str(e))
        raise


def load_text_file(file_path: Union[str, Path], encoding: str = 'utf-8') -> str:
    """Load text content from a file with standardized error handling and logging.

    Args:
        file_path: Path to the text file
        encoding: File encoding to use

    Returns:
        str: The loaded text content

    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file cannot be read
    """
    try:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, 'r', encoding=encoding) as f:
            content = f.read()

        logger.info("Loaded text file from: %s", file_path)
        return content

    except Exception as e:
        logger.error("Error loading text file from %s: %s", file_path, str(e))
        raise


def find_latest_file(directory: Union[str, Path], pattern: str = '*.json') -> Optional[Path]:
    """Find the most recent file matching a pattern in a directory.

    Args:
        directory: Directory to search in
        pattern: File pattern to match (e.g., '*.json')

    Returns:
        Optional[Path]: Path to the most recent file, or None if no files found
    """
    try:
        directory = Path(directory)
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        files = list(directory.glob(pattern))
        if not files:
            return None

        return max(files, key=lambda x: x.stat().st_mtime)

    except Exception as e:
        logger.error("Error finding latest file in %s: %s", directory, str(e))
        raise


def load_newsletter_file(date_str: Optional[str] = None, file_path: Optional[Union[str, Path]] = None,
                         newsletter_type: str = 'daily_morning') -> Tuple[Dict, str, Path]:
    """Load a newsletter file with standardized error handling and logging.

    Args:
        date_str: Date string in YYYY-MM-DD format. If None, use current date
        file_path: Path to the newsletter file. If None, find the most recent file
        newsletter_type: Type of newsletter (e.g., 'daily_morning')

    Returns:
        Tuple[Dict, str, Path]: Tuple containing the newsletter content, date string, and file path

    Raises:
        FileNotFoundError: If no newsletter file found
        ValueError: If newsletter content is invalid
    """
    try:
        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')

        newsletters_dir = Path('src/outputs/newsletters') / newsletter_type

        # If file path is provided, use it
        if file_path:
            input_file = Path(file_path)
        else:
            # Try to find file for the specified date
            base_filename = f'{newsletter_type}_{date_str}'
            input_file = newsletters_dir / f'{base_filename}.json'

            # If no file exists for the date, find the most recent file
            if not input_file.exists():
                input_file = find_latest_file(
                    newsletters_dir, f'{newsletter_type}_*.json')
                if not input_file:
                    raise FileNotFoundError(
                        f"No newsletter files found in {newsletters_dir}")

        content = load_json_file(input_file)
        return content, date_str, input_file

    except Exception as e:
        logger.error("Error loading newsletter file: %s", str(e))
        raise


def load_news_articles(date_str: Optional[str] = None) -> Tuple[List[Dict], str]:
    """Load news articles from a JSON file with standardized error handling and logging.

    Args:
        date_str: Date string in YYYY-MM-DD format. If None, use most recent file

    Returns:
        Tuple[List[Dict], str]: Tuple containing the articles list and date string

    Raises:
        FileNotFoundError: If no news articles file found
        ValueError: If articles content is invalid
    """
    try:
        news_dir = Path('src/outputs/news/json')

        if date_str:
            file_path = news_dir / f'news_articles_{date_str}.json'
            if not file_path.exists():
                raise FileNotFoundError(
                    f"No news articles file found for date: {date_str}")
        else:
            # Find the most recent file
            file_path = find_latest_file(news_dir, 'news_articles_*.json')
            if not file_path:
                raise FileNotFoundError("No news articles files found")
            date_str = file_path.stem.split('_')[-1]

        articles = load_json_file(file_path)
        if not isinstance(articles, list):
            raise ValueError(
                f"Invalid articles content in {file_path}: expected list, got {type(articles)}")

        logger.info("Loaded %d articles from %s", len(articles), file_path)
        return articles, date_str

    except Exception as e:
        logger.error("Error loading news articles: %s", str(e))
        raise


def load_formatted_newsletter(date_str: Optional[str] = None, newsletter_type: str = 'daily_morning') -> Tuple[str, str, Path]:
    """Load a formatted newsletter HTML file with standardized error handling and logging.

    Args:
        date_str: Date string in YYYY-MM-DD format. If None, use most recent file
        newsletter_type: Type of newsletter (e.g., 'daily_morning')

    Returns:
        Tuple[str, str, Path]: Tuple containing the HTML content, date string, and file path

    Raises:
        FileNotFoundError: If no formatted newsletter file found
    """
    try:
        formatted_dir = Path(
            'src/outputs/formatted_newsletters') / newsletter_type

        if date_str:
            file_path = formatted_dir / f'{newsletter_type}_{date_str}.html'
            if not file_path.exists():
                raise FileNotFoundError(
                    f"No formatted newsletter file found for date: {date_str}")
        else:
            # Find the most recent file
            file_path = find_latest_file(
                formatted_dir, f'{newsletter_type}_*.html')
            if not file_path:
                raise FileNotFoundError("No formatted newsletter files found")
            date_str = file_path.stem.split('_')[-1]

        content = load_text_file(file_path)
        return content, date_str, file_path

    except Exception as e:
        logger.error("Error loading formatted newsletter: %s", str(e))
        raise


def extract_date_from_filename(filename: Union[str, Path]) -> Tuple[Optional[str], Optional[int]]:
    """Extract date and increment from a filename.

    Args:
        filename: The filename to extract date from

    Returns:
        Tuple[Optional[str], Optional[int]]: A tuple containing the date string (YYYY-MM-DD) and increment number
    """
    try:
        # Convert Path to string if needed
        filename_str = str(filename)

        # Try to match date pattern with optional increment
        match = re.search(r'(\d{4}-\d{2}-\d{2})(?:_(\d+))?', filename_str)
        if match:
            date_str = match.group(1)
            increment = int(match.group(2)) if match.group(2) else 1
            return date_str, increment
        return None, None
    except Exception as e:
        logger.error("Error extracting date from filename %s: %s",
                     filename, str(e))
        return None, None
