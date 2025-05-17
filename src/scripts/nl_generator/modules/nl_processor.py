#!/usr/bin/env python3
"""
Module for processing newsletters with article matching and impact generation.
"""
from typing import Dict, Optional

from nl_utils.logger_config import get_logger, get_module_name
from nl_utils.file_handler import FileHandler, FileType

from .matcher import Matcher
from .impact_generator import ImpactGenerator
from .impact_inserter import ImpactInserter


class NLProcessor:
    """Class for processing newsletters with article matching and impact generation."""

    def __init__(self, debug_mode: bool = False):
        """Initialize the NLProcessor.

        Args:
            debug_mode (bool): Whether to run in debug mode.
        """
        self.logger = get_logger(get_module_name(__name__))
        self.debug_mode = debug_mode
        self.file_handler = FileHandler()
        self.matcher = Matcher(debug_mode)
        self.impact_generator = ImpactGenerator(debug_mode)
        self.impact_inserter = ImpactInserter(debug_mode)

    def run_matching(self, newsletter: Dict, article_groups: Dict, date_str: str) -> Optional[str]:
        """Run only the matching process on a newsletter.

        Args:
            newsletter (Dict): The newsletter content.
            article_groups (Dict): The article groups.
            date_str (str): Date string in YYYY-MM-DD format.

        Returns:
            Optional[str]: Path to the processed newsletter file.
        """
        try:
            self.logger.info("Running matching process")

            # Match news items with article groups
            matched_newsletter = self.matcher.match_news_items(
                newsletter, article_groups)

            # Save matched newsletter
            return self.save_newsletter(matched_newsletter, date_str)

        except Exception as e:
            self.logger.error("Error in matching process: %s", str(e))
            return None

    def process_newsletter(self, unprocessed_newsletter: Dict, article_groups: Dict, ignore_impacts: bool = False, ignore_matching: bool = False) -> Dict:
        """Process the newsletter with article matching and impact generation.

        Args:
            unprocessed_newsletter (Dict): The newsletter content.
            article_groups (Dict): The article groups.
            ignore_impacts (bool): Whether to skip impact generation and return placeholders.
            ignore_matching (bool): Whether to skip matching process.
        Returns:
            Dict: Processed newsletter.
        """
        try:
            self.logger.info(
                "Processing newsletter (ignore_impacts=%s)", ignore_impacts)

            # Match news items with article groups
            if not ignore_matching:
                matched_newsletter = self.matcher.match_news_items(
                    unprocessed_newsletter, article_groups)
            else:
                matched_newsletter = unprocessed_newsletter

            if ignore_impacts:
                self.logger.info("Setting impacts to NULL for all news items")
                # Set impacts and URLs to NULL for all news items
                for category in matched_newsletter:
                    if category in ['closing_summary', 'main_headline', 'summary']:
                        continue
                    for item in matched_newsletter[category]:
                        item['impact'] = None
                        item['impact_urls'] = []
                matched_newsletter['summary_impact'] = None
                matched_newsletter['summary_impact_urls'] = []
                return matched_newsletter

            # Generate impacts
            newsletter_with_impacts = self.impact_generator.generate_impacts(
                matched_newsletter, ignore_impacts)

            # Insert impacts
            processed_newsletter = self.impact_inserter.insert_impacts(
                newsletter_with_impacts)

            return processed_newsletter

        except Exception as e:
            self.logger.error("Error processing newsletter: %s", str(e))
            return unprocessed_newsletter

    def save_newsletter(self, newsletter: Dict, date_str: str) -> Optional[str]:
        """Save the processed newsletter to a JSON file.

        Args:
            newsletter (Dict): The newsletter content.
            date_str (str): The date string to use in the filename.

        Returns:
            Optional[str]: Path to the saved newsletter file.
        """
        try:
            # Save the processed newsletter
            file_path = self.file_handler.save_file(
                content=newsletter,
                file_type=FileType.PROCESSED_NEWSLETTER,
                date_str=date_str,
                base_name="newsletter_processed"
            )

            self.logger.info("Saved processed newsletter to: %s", file_path)
            return str(file_path)

        except Exception as e:
            self.logger.error("Error saving newsletter: %s", str(e))
            return None

    def run_processor(self, date_str: str, ignore: bool = False, ignore_impacts: bool = False, ignore_matching: bool = False) -> Optional[str]:
        """Run the newsletter processing.

        Args:
            date_str (str): Date string in YYYY-MM-DD format.
            ignore (bool): Whether to ignore all operations.
            ignore_impacts (bool): Whether to skip impact generation and return placeholders.
            ignore_matching (bool): Whether to skip matching process.

        Returns:
            Optional[str]: Path to the processed newsletter file.
        """
        if ignore:
            self.logger.info("Ignoring newsletter processing")
            return "src/outputs/newsletters/processed/dummy.json"

        try:
            # Load unprocessed newsletter
            newsletter = self.file_handler.load_file(
                FileType.UNPROCESSED_NEWSLETTER,
                date_str=date_str,
                base_name="newsletter_unprocessed"
            )
            if not newsletter:
                self.logger.error(
                    "No unprocessed newsletter found for date: %s", date_str)
                return None

            # Load article groups
            article_groups = self.file_handler.load_file(
                FileType.ARTICLE_GROUPS,
                date_str=date_str,
                base_name="article_groups"
            )
            if not article_groups:
                self.logger.error(
                    "No article groups found for date: %s", date_str)
                return None

            # Process newsletter
            processed_newsletter = self.process_newsletter(
                newsletter, article_groups, ignore_impacts, ignore_matching)

            # Save processed newsletter
            return self.save_newsletter(processed_newsletter, date_str)

        except Exception as e:
            self.logger.error("Error in newsletter processing: %s", str(e))
            return None
