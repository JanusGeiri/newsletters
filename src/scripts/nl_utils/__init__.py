"""
Utility functions and configurations package.
"""

from .save_file import (
    save_json_file,
    save_text_file,
    save_newsletter_json,
    save_formatted_newsletter,
    save_news_articles
)

from .load_file import (
    load_json_file,
    load_text_file,
    find_latest_file,
    load_newsletter_file,
    load_news_articles,
    load_formatted_newsletter,
    extract_date_from_filename
)

from .scraper_utils import (
    save_debug_html,
    save_combined_articles,
    ensure_output_dirs
)

from .date_utils import (
    get_yesterday_date
)

__all__ = [
    'save_json_file',
    'save_text_file',
    'save_newsletter_json',
    'save_formatted_newsletter',
    'save_news_articles',
    'load_json_file',
    'load_text_file',
    'find_latest_file',
    'load_newsletter_file',
    'load_news_articles',
    'load_formatted_newsletter',
    'extract_date_from_filename',
    'save_debug_html',
    'save_combined_articles',
    'ensure_output_dirs'
]
