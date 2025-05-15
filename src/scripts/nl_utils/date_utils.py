"""
Utility functions for date handling and manipulation.

This module provides helper functions for working with dates, including
getting yesterday's date in a standardized format.
"""
from datetime import datetime, timedelta


def get_yesterday_date():
    """Get yesterday's date in YYYY-MM-DD format."""
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime('%Y-%m-%d')
