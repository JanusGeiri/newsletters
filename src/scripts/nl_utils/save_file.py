"""
Standardized file saving utilities for the newsletter system.
"""
import json
from pathlib import Path
from typing import Union, Dict, List
from .logger_config import get_logger

logger = get_logger('file_utils')


def save_json_file(data: Union[Dict, List], file_path: Union[str, Path], ensure_ascii: bool = False, indent: int = 2) -> Path:
    """Save data to a JSON file with standardized error handling and logging.

    Args:
        data: The data to save (dict or list)
        file_path: Path where to save the file
        ensure_ascii: Whether to ensure ASCII output
        indent: Number of spaces for indentation

    Returns:
        Path: Path to the saved file

    Raises:
        ValueError: If data is not a dict or list
        IOError: If file cannot be written
    """
    try:
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if not isinstance(data, (dict, list)):
            raise ValueError("Data must be a dictionary or list")

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=ensure_ascii, indent=indent)

        logger.info("Saved JSON file to: %s", file_path)
        return file_path

    except Exception as e:
        logger.error("Error saving JSON file to %s: %s", file_path, str(e))
        raise


def save_text_file(content: str, file_path: Union[str, Path], encoding: str = 'utf-8') -> Path:
    """Save text content to a file with standardized error handling and logging.

    Args:
        content: The text content to save
        file_path: Path where to save the file
        encoding: File encoding to use

    Returns:
        Path: Path to the saved file

    Raises:
        IOError: If file cannot be written
    """
    try:
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)

        logger.info("Saved text file to: %s", file_path)
        return file_path

    except Exception as e:
        logger.error("Error saving text file to %s: %s", file_path, str(e))
        raise


def save_newsletter_json(newsletter_content: Union[str, Dict], date_str: str, newsletter_type: str = 'daily_morning') -> Path:
    """Save newsletter content to a JSON file with standardized naming and directory structure.

    Args:
        newsletter_content: The newsletter content (string or dict)
        date_str: Date string in YYYY-MM-DD format
        newsletter_type: Type of newsletter (e.g., 'daily_morning')

    Returns:
        Path: Path to the saved newsletter file
    """
    try:
        # Create base newsletters directory
        newsletters_dir = Path('src/outputs/newsletters') / newsletter_type
        newsletters_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        base_filename = f'{newsletter_type}_{date_str}'
        output_file = newsletters_dir / f'{base_filename}.json'

        # Convert string to dict if needed
        if isinstance(newsletter_content, str):
            try:
                newsletter_content = json.loads(newsletter_content)
            except json.JSONDecodeError as e:
                logger.error(
                    "Failed to parse newsletter content as JSON: %s", str(e))
                raise

        return save_json_file(newsletter_content, output_file)

    except Exception as e:
        logger.error("Error saving newsletter: %s", str(e))
        raise


def save_formatted_newsletter(html_content: str, date_str: str, newsletter_type: str = 'daily_morning') -> Path:
    """Save formatted newsletter HTML to a file with standardized naming and directory structure.

    Args:
        html_content: The HTML content to save
        date_str: Date string in YYYY-MM-DD format
        newsletter_type: Type of newsletter (e.g., 'daily_morning')

    Returns:
        Path: Path to the saved HTML file
    """
    try:
        # Create formatted newsletters directory
        formatted_dir = Path(
            'src/outputs/formatted_newsletters') / newsletter_type
        formatted_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        base_filename = f'{newsletter_type}_{date_str}'
        output_file = formatted_dir / f'{base_filename}.html'

        return save_text_file(html_content, output_file)

    except Exception as e:
        logger.error("Error saving formatted newsletter: %s", str(e))
        raise


def save_news_articles(articles: List[Dict], date_str: str) -> Path:
    """Save news articles to a JSON file with standardized naming and directory structure.

    Args:
        articles: List of article dictionaries
        date_str: Date string in YYYY-MM-DD format

    Returns:
        Path: Path to the saved articles file
    """
    try:
        # Create news articles directory
        news_dir = Path('src/outputs/news/json')
        news_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        output_file = news_dir / f'news_articles_{date_str}.json'

        return save_json_file(articles, output_file)

    except Exception as e:
        logger.error("Error saving news articles: %s", str(e))
        raise
