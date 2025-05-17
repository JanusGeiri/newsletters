#!/usr/bin/env python3
"""
Module for inserting impacts into newsletter items.
"""
from typing import Dict

from nl_utils.logger_config import get_logger, get_module_name
from nl_utils.file_handler import FileHandler


class ImpactInserter:
    """Class for inserting impacts into newsletter items."""

    def __init__(self, debug_mode: bool = False):
        """Initialize the ImpactInserter.

        Args:
            debug_mode (bool): Whether to run in debug mode.
        """
        self.logger = get_logger(get_module_name(__name__))
        self.debug_mode = debug_mode
        self.file_handler = FileHandler()

    def insert_impacts(self, newsletter: Dict) -> Dict:
        """Insert impacts into newsletter items.

        Args:
            newsletter (Dict): The newsletter content with impacts.

        Returns:
            Dict: Newsletter with inserted impacts.
        """
        try:
            self.logger.info("Inserting impacts into newsletter items")

            # Process each category
            for category in newsletter:
                if not isinstance(newsletter[category], list):
                    continue

                for item in newsletter[category]:
                    if not isinstance(item, dict):
                        continue

                    # Get impact and URLs
                    impact = item.get('impact')
                    impact_urls = item.get('impact_urls', [])

                    if not impact:
                        continue

                    # Insert impact into description
                    description = item.get('description', '')
                    if description:
                        # Add impact section if not already present
                        if 'Áhrif:' not in description:
                            item['description'] = f"{description}\n\nÁhrif: {impact}"
                        else:
                            # Replace existing impact section
                            parts = description.split('Áhrif:')
                            item['description'] = f"{parts[0]}Áhrif: {impact}"

                    # Add impact URLs to the item's URLs
                    item['urls'] = list(
                        set(item.get('urls', []) + impact_urls))

            return newsletter

        except Exception as e:
            self.logger.error("Error inserting impacts: %s", str(e))
            return newsletter
