#!/usr/bin/env python3
"""
Module for generating impacts for newsletter items.
"""
from typing import Dict

from nl_utils.logger_config import get_logger, get_module_name
from nl_utils.file_handler import FileHandler, FileType


class ImpactGenerator:
    """Class for generating impacts for newsletter items."""

    def __init__(self, debug_mode: bool = False):
        """Initialize the ImpactGenerator.

        Args:
            debug_mode (bool): Whether to run in debug mode.
        """
        self.logger = get_logger(get_module_name(__name__))
        self.debug_mode = debug_mode
        self.file_handler = FileHandler()

    def generate_impacts(self, newsletter: Dict, ignore_impacts: bool = False) -> Dict:
        """Generate impacts for newsletter items.

        Args:
            newsletter (Dict): The newsletter content.
            ignore_impacts (bool): Whether to skip impact generation and return placeholders.

        Returns:
            Dict: Newsletter with generated impacts.
        """
        try:
            self.logger.info("Generating impacts for newsletter items")

            if ignore_impacts:
                # Set placeholder impacts for all items
                for category in newsletter:
                    if isinstance(newsletter[category], list):
                        for item in newsletter[category]:
                            if isinstance(item, dict):
                                item['impact'] = "Impact analysis skipped"
                                item['impact_urls'] = []
                return newsletter

            # Process each category
            for category in newsletter:
                if not isinstance(newsletter[category], list):
                    continue

                for item in newsletter[category]:
                    if not isinstance(item, dict):
                        continue

                    # Get the matched group ID
                    match = item.get('match', {})
                    group_id = match.get('group_id')

                    if not group_id:
                        self.logger.warning(
                            "No group ID found for item: %s", item.get('title', 'Unknown'))
                        continue

                    # Load article group
                    article_groups = self.file_handler.load_file(
                        FileType.ARTICLE_GROUPS,
                        date_str=newsletter.get('date'),
                        base_name="article_groups"
                    )

                    if not article_groups:
                        self.logger.error("No article groups found")
                        continue

                    # Find the matching group
                    group = next(
                        (g for g in article_groups.get('groups', [])
                         if g['details']['group_number'] == group_id),
                        None
                    )

                    if not group:
                        self.logger.warning(
                            "Group not found: %s", group_id)
                        continue

                    # Generate impact based on group details
                    impact = self._generate_impact_for_group(group)
                    item['impact'] = impact
                    item['impact_urls'] = group.get('urls', [])

            return newsletter

        except Exception as e:
            self.logger.error("Error generating impacts: %s", str(e))
            return newsletter

    def _generate_impact_for_group(self, group: Dict) -> str:
        """Generate impact text for a group of articles.

        Args:
            group (Dict): The article group to generate impact for.

        Returns:
            str: Generated impact text.
        """
        try:
            article_count = group['details'].get('article_count', 0)
            if article_count == 0:
                return "No articles found in group"

            # Generate impact based on article count and sources
            sources = set(article['source']
                          for article in group['details'].get('articles', []))
            source_count = len(sources)

            if article_count == 1:
                return f"Single article from {next(iter(sources))}"
            elif source_count == 1:
                return f"{article_count} articles from {next(iter(sources))}"
            else:
                return f"{article_count} articles from {source_count} different sources"

        except Exception as e:
            self.logger.error("Error generating impact for group: %s", str(e))
            return "Error generating impact"
