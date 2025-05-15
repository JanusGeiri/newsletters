"""
News scraper implementations for various sources.
"""
from .base_scraper import NewsScraper
from .visir_scraper import VisirScraper
from .mbl_scraper import MblScraper
from .vb_scraper import VbScraper
from .ruv_scraper import RUVScraper

__all__ = [
    'NewsScraper',
    'VisirScraper',
    'MblScraper',
    'VbScraper',
    'RUVScraper'
]
