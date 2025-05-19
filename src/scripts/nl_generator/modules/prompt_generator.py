#!/usr/bin/env python3
"""
Module for generating prompts for newsletter generation.
"""
import random
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from nl_utils.logger_config import get_logger, get_module_name
from nl_utils.file_handler import FileHandler, FileType


class PromptGenerator:
    """Class for generating prompts for newsletter generation."""

    def __init__(self, debug_mode: bool = False):
        """Initialize the PromptGenerator.

        Args:
            debug_mode (bool): Whether to run in debug mode.
        """
        self.logger = get_logger(get_module_name(__name__))
        self.debug_mode = debug_mode
        self.file_handler = FileHandler()

    def load_previous_newsletter(self, date_str: str) -> str:
        """Load and format the previous day's newsletter content.

        Args:
            date_str (str): Current date string in YYYY-MM-DD format.

        Returns:
            str: Formatted previous newsletter content.
        """
        try:
            # Calculate previous day's date
            current_date = datetime.strptime(date_str, '%Y-%m-%d')
            previous_date = current_date - timedelta(days=1)
            previous_date_str = previous_date.strftime('%Y-%m-%d')

            # Load the previous newsletter
            previous_newsletter = self.file_handler.load_file(
                FileType.PROCESSED_NEWSLETTER,
                date_str=previous_date_str,
                base_name="newsletter_processed"
            )

            if not previous_newsletter:
                self.logger.warning("No previous newsletter found for date: %s", previous_date_str)
                return "No previous newsletter available."

            # Format the content sections
            formatted_sections = []

            # Add key events
            if 'key_events' in previous_newsletter:
                formatted_sections.append("\nMikilvægustu fréttirnar:")
                for event in previous_newsletter['key_events']:
                    formatted_sections.append(f"\n{event['title']}\n{event['description']}")

            # Add domestic news
            if 'domestic_news' in previous_newsletter:
                formatted_sections.append("\nInnlent:")
                for news in previous_newsletter['domestic_news']:
                    formatted_sections.append(f"\n{news['title']}\n{news['description']}")

            # Add foreign news
            if 'foreign_news' in previous_newsletter:
                formatted_sections.append("\nErlent:")
                for news in previous_newsletter['foreign_news']:
                    formatted_sections.append(f"\n{news['title']}\n{news['description']}")

            # Add business news
            if 'business' in previous_newsletter:
                formatted_sections.append("\nViðskipti:")
                for news in previous_newsletter['business']:
                    formatted_sections.append(f"\n{news['title']}\n{news['description']}")

            # Add famous people news
            if 'famous_people' in previous_newsletter:
                formatted_sections.append("\nFræga fólkið:")
                for news in previous_newsletter['famous_people']:
                    formatted_sections.append(f"\n{news['title']}\n{news['description']}")

            # Add sports news
            if 'sports' in previous_newsletter:
                formatted_sections.append("\nÍþróttir:")
                for news in previous_newsletter['sports']:
                    formatted_sections.append(f"\n{news['title']}\n{news['description']}")

            # Add arts news
            if 'arts' in previous_newsletter:
                formatted_sections.append("\nListir:")
                for news in previous_newsletter['arts']:
                    formatted_sections.append(f"\n{news['title']}\n{news['description']}")

            # Add science news
            if 'science' in previous_newsletter:
                formatted_sections.append("\nVísindi:")
                for news in previous_newsletter['science']:
                    formatted_sections.append(f"\n{news['title']}\n{news['description']}")

            return "\n".join(formatted_sections)

        except Exception as e:
            self.logger.error("Error loading previous newsletter: %s", str(e))
            return "Error loading previous newsletter."

    def format_article_groups_for_prompt(self, article_groups: List[Dict]) -> str:
        """Format article groups into a string for the prompt.

        Args:
            article_groups (List[Dict]): List of article groups to format.

        Returns:
            str: Formatted article groups string.
        """
        if not article_groups:
            self.logger.warning("No article groups provided")
            return "No article groups available."

        try:
            # Get the date from the article groups
            date_str = article_groups.get('date', 'Unknown date')
            if date_str == 'Unknown date':
                self.logger.error("Could not find date in article groups")
                return "Error: No date found in article groups."

            date_header = f"Date: {date_str}"
            formatted_groups = [date_header]

            # Load all articles for the date
            articles = self.file_handler.load_file(
                FileType.ARTICLES,
                date_str=date_str,
                base_name="articles"
            )
            if not articles:
                self.logger.error("No articles found for date: %s", date_str)
                return "No articles available."

            # Create a lookup dictionary for articles by ID
            article_lookup = {article['article_id']: article for article in articles}

            # Get the groups from the article_groups structure
            groups = article_groups.get('groups', [])
            if not groups:
                self.logger.error("No groups found in article groups")
                return "Error: No groups found in article groups."

            # Validate and shuffle groups
            if not isinstance(groups, list):
                self.logger.error("Groups is not a list: %s", type(groups))
                return "Error: Invalid groups format."

            # Randomize the order of groups
            try:
                shuffled_groups = random.sample(groups, len(groups))
            except ValueError as e:
                self.logger.error("Error shuffling groups: %s", str(e))
                # Fallback to original order if shuffling fails
                shuffled_groups = groups

            # Process each group
            for group in shuffled_groups:
                if not isinstance(group, dict):
                    self.logger.warning(
                        "Invalid group format: %s", type(group))
                    continue

                # Get group number from details
                group_number = group.get('details', {}).get(
                    'group_number', 'Unknown')
                formatted_group = f"\n{'='*80}\nGROUP {group_number}\n{'='*80}\n"

                # Get article IDs from the group
                article_ids = group.get('article_ids', [])
                if not article_ids:
                    self.logger.warning(
                        "No article IDs found in group %s", group_number)
                    continue

                # Process each article in the group
                for article_id in article_ids:
                    article = article_lookup.get(article_id)
                    if not article:
                        self.logger.warning(
                            "Article not found: %s", article_id)
                        continue

                    # Article delimiter
                    formatted_group += f"\n{'-'*40}\n"
                    formatted_group += f"Title: {article.get('article_title', 'No title')}\n"
                    formatted_group += f"Content: {article.get('article_text', 'No content')}\n"
                    formatted_group += f"{'-'*40}\n"

                formatted_groups.append(formatted_group)

            if len(formatted_groups) <= 1:  # Only contains the date header
                self.logger.warning("No valid groups were processed")
                return "No valid article groups to process."

            return "\n".join(formatted_groups)

        except Exception as e:
            self.logger.error("Error formatting article groups: %s", str(e))
            return "Error formatting article groups."

    def load_prompt_template(self, date_str: str, formatted_article_groups: str) -> str:
        """Load and format the newsletter prompt template.

        Args:
            date_str (str): Date string in YYYY-MM-DD format.
            formatted_article_groups (str): Formatted article groups string.

        Returns:
            str: The formatted prompt template.
        """
        try:
            # Load the base prompt template
            base_template = self.file_handler.load_file(
                FileType.PROMPT,
                base_name="base_newsletter_prompt"
            )

            # Load previous newsletter content
            previous_newsletter_content = self.load_previous_newsletter(date_str)

            # Format the template with the provided data
            prompt = base_template.format(
                date=date_str,
                article_groups=formatted_article_groups,
                previous_newsletter_content=previous_newsletter_content
            )

            return prompt

        except Exception as e:
            self.logger.error("Error loading prompt template: %s", str(e))
            raise

    def generate_prompt(self, article_groups: List[Dict], date_str: str) -> Optional[str]:
        """Generate a prompt for newsletter generation.

        Args:
            article_groups (List[Dict]): List of article groups to include in the prompt.
            date_str (str): Date string in YYYY-MM-DD format.

        Returns:
            Optional[str]: The generated prompt.
        """
        try:
            self.logger.info("Generating prompt for %s", date_str)
            formatted_article_groups = self.format_article_groups_for_prompt(
                article_groups)

            prompt = self.load_prompt_template(
                date_str, formatted_article_groups)

            # Save the generated prompt
            self.file_handler.save_file(
                content=prompt,
                file_type=FileType.TEXT,
                date_str=date_str,
                base_name="generated_prompt"
            )

            return prompt

        except Exception as e:
            self.logger.error("Error generating prompt: %s", str(e))
            return None
