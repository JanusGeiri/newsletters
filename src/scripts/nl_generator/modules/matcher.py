#!/usr/bin/env python3
"""
Module for matching news items with article groups.
"""
from typing import Dict, Set, Tuple, Optional

from nl_utils.logger_config import get_logger, get_module_name
from nl_utils.file_handler import FileHandler, FileType
from nl_article_processor.text_processor import TextProcessor
from nl_article_processor.similarity_strategies import (
    JaccardSimilarity
)


class Matcher:
    """Class for matching news items with article groups."""

    def __init__(self, debug_mode: bool = False):
        """Initialize the Matcher.

        Args:
            debug_mode (bool): Whether to run in debug mode.
        """
        self.logger = get_logger(get_module_name(__name__))
        self.debug_mode = debug_mode
        self.file_handler = FileHandler()
        self.text_processor = TextProcessor(debug_mode=debug_mode)
        self.similarity_strategy = JaccardSimilarity()

        # Initialize article storage
        self.articles = None
        self.articles_dict = None
        self.current_date = None

    def _load_articles(self, date_str: str) -> None:
        """Load articles for a specific date.

        Args:
            date_str (str): The date string in YYYY-MM-DD format.
        """
        if self.current_date == date_str and self.articles is not None:
            return

        self.articles = self.file_handler.load_file(
            FileType.ARTICLES,
            date_str=date_str,
            base_name="articles"
        )
        if not self.articles:
            self.logger.error(
                "Failed to load articles file for date: %s", date_str)
            self.articles = []
            self.articles_dict = {}
            return

        self.articles_dict = {article.get(
            'article_id'): article for article in self.articles}
        self.current_date = date_str
        self.logger.debug("Loaded %d articles for date: %s",
                          len(self.articles), date_str)

    def _extract_news_item_text(self, news_item: Dict) -> str:
        """Extract all text from a news item for lemma processing.

        Args:
            news_item (Dict): The news item to extract text from.

        Returns:
            str: Combined text from the news item.
        """
        text_parts = []

        # Add title
        if 'title' in news_item:
            text_parts.append(news_item['title'])

        # Add description
        if 'description' in news_item:
            text_parts.append(news_item['description'])

        # Add TLDR if it exists
        if 'tldr' in news_item:
            text_parts.append(news_item['tldr'])

        return ' '.join(text_parts)

    def _process_news_items(self, newsletter: Dict) -> Dict[str, Set[str]]:
        """Process all news items in the newsletter to extract lemmas.

        Args:
            newsletter (Dict): The newsletter content.

        Returns:
            Dict[str, Set[str]]: Dictionary mapping news item keys to their lemmas.
        """
        news_item_lemmas = {}

        # Process main headline
        if 'main_headline' in newsletter:
            lemmas = self.text_processor.extract_lemmas(
                newsletter['main_headline'], 'newsletter')
            news_item_lemmas['main_headline'] = set(lemmas)

        # Process summary
        if 'summary' in newsletter:
            lemmas = self.text_processor.extract_lemmas(
                newsletter['summary'], 'newsletter')
            news_item_lemmas['summary'] = set(lemmas)

        # Process key events
        if 'key_events' in newsletter:
            for i, event in enumerate(newsletter['key_events']):
                text = self._extract_news_item_text(event)
                lemmas = self.text_processor.extract_lemmas(text, 'newsletter')
                news_item_lemmas[f'key_event_{i}'] = set(lemmas)

        # Process other categories
        categories = [
            'domestic_news', 'foreign_news', 'business',
            'famous_people', 'sports', 'arts', 'science'
        ]

        for category in categories:
            if category in newsletter:
                for i, item in enumerate(newsletter[category]):
                    text = self._extract_news_item_text(item)
                    lemmas = self.text_processor.extract_lemmas(
                        text, 'newsletter')
                    news_item_lemmas[f'{category}_{i}'] = set(lemmas)

        return news_item_lemmas

    def _find_best_matching_group(
        self,
        news_item_lemmas: Set[str],
        article_groups: Dict,
        similarity_threshold: float = 0.3
    ) -> Tuple[Optional[str], float]:
        """Find the best matching article group for a news item.

        Args:
            news_item_lemmas (Set[str]): Lemmas from the news item.
            article_groups (Dict): The article groups to match against.
            similarity_threshold (float): Minimum similarity score to consider a match.

        Returns:
            Tuple[Optional[str], float]: Best matching group ID and similarity score.
        """
        best_match = None
        best_score = 0.0

        # Get the groups list from the article_groups dictionary
        groups = article_groups.get('groups', [])
        if not isinstance(groups, list):
            self.logger.error(
                "Article groups 'groups' is not a list: %s", type(groups))
            return None, 0.0

        self.logger.debug("Found %d groups to match against", len(groups))

        # Load articles if needed
        self._load_articles(article_groups.get('date'))
        self.logger.debug("Loaded %d articles", len(
            self.articles) if self.articles else 0)

        for group in groups:
            if not isinstance(group, dict):
                self.logger.warning(
                    "Group is not a dictionary: %s", type(group))
                continue

            group_lemmas = set()

            # Collect all lemmas from articles in the group
            article_ids = group.get('article_ids', [])
            if not isinstance(article_ids, list):
                self.logger.warning(
                    "Group article_ids is not a list: %s", type(article_ids))
                continue

            self.logger.debug(
                "Processing group with %d article IDs", len(article_ids))

            for article_id in article_ids:
                article = self.articles_dict.get(article_id)
                if article:
                    article_lemmas = article.get('article_lemmas', [])
                    if article_lemmas:
                        group_lemmas.update(article_lemmas)
                    else:
                        self.logger.debug(
                            "Article %s has no lemmas", article_id)
                else:
                    self.logger.debug(
                        "Article %s not found in articles dictionary", article_id)

            # Calculate similarity
            if group_lemmas:
                self.logger.debug("Group has %d lemmas", len(group_lemmas))
                similarity = self.similarity_strategy.calculate_similarity(
                    news_item_lemmas, group_lemmas)
                self.logger.debug("Similarity score: %.2f", similarity)

                if similarity > best_score and similarity >= similarity_threshold:
                    best_score = similarity
                    group_details = group.get('details', {})
                    best_match = group_details.get('group_number')
                    self.logger.debug(
                        "New best match: group %s with score %.2f", best_match, best_score)
            else:
                self.logger.debug("Group has no lemmas to compare")

        if best_match is None:
            self.logger.debug(
                "No match found above threshold %.2f", similarity_threshold)
        else:
            self.logger.debug(
                "Final best match: group %s with score %.2f", best_match, best_score)

        return best_match, best_score

    def _insert_group_info(self, matched_newsletter: Dict, article_groups: Dict) -> Dict:
        """Insert article group information and URLs into matched news items.

        Args:
            matched_newsletter (Dict): The newsletter with matched items.
            article_groups (Dict): The article groups containing URLs.

        Returns:
            Dict: Newsletter with inserted group information and URLs.
        """
        # Load articles if needed
        self._load_articles(article_groups.get('date'))

        # Create a dictionary for quick group lookup
        groups_dict = {
            group.get('details', {}).get('group_number'): group
            for group in article_groups.get('groups', [])
        }

        # Define categories to process
        categories = [
            'key_events',  # Key stories
            'domestic_news',
            'foreign_news',
            'business',
            'famous_people',
            'sports',
            'arts',
            'science'
        ]

        for category in categories:
            if category not in matched_newsletter:
                continue

            for item in matched_newsletter[category]:
                if 'match' not in item:
                    continue

                group_id = item['match'].get('group_id')
                if not group_id:
                    item['article_urls'] = []
                    continue

                # Get the group from our lookup dictionary
                group = groups_dict.get(group_id)

                # Get article URLs for this group
                article_urls = group.get('urls', [])

                # Insert group information and URLs
                item['article_urls'] = article_urls

                self.logger.debug(
                    "Inserted group info for %s item with group %s (%d URLs)",
                    category, group_id, len(article_urls))

        return matched_newsletter

    def match_news_items(self, newsletter: Dict, article_groups: Dict) -> Dict:
        """Match news items with article groups.

        Args:
            newsletter (Dict): The newsletter content.
            article_groups (Dict): The article groups.

        Returns:
            Dict: Newsletter with matched article groups.
        """
        try:
            self.logger.info("Matching news items with article groups")

            # Create a copy of the newsletter to modify
            matched_newsletter = newsletter.copy()

            # Define categories to match
            categories = [
                '', 'key_events'  # Key stories
                , 'domestic_news', 'foreign_news', 'business', 'famous_people', 'sports', 'arts', 'science'
            ]

            # Match each category
            for category in categories:
                if category not in matched_newsletter:
                    continue

                self.logger.info("Matching items in category: %s", category)

                # Process each item in the category
                for i, item in enumerate(matched_newsletter[category]):
                    # Extract text from the news item
                    text = self._extract_news_item_text(item)

                    # Process text to get lemmas
                    lemmas = self.text_processor.extract_lemmas(
                        text, 'newsletter')

                    # Find best matching group
                    group_id, similarity = self._find_best_matching_group(
                        set(lemmas), article_groups)

                    # Always add match information, even if no match was found
                    matched_newsletter[category][i]['match'] = {
                        'group_id': group_id,
                        'similarity': similarity
                    }
                    self.logger.debug(
                        "Added match info for %s item %d: group %s (similarity: %.2f)",
                        category, i, group_id, similarity)

            # Insert group information and URLs
            matched_newsletter = self._insert_group_info(
                matched_newsletter, article_groups)

            return matched_newsletter

        except Exception as e:
            self.logger.error("Error matching news items: %s", str(e))
            return newsletter
