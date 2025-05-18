#!/usr/bin/env python3
"""
Module for matching news items with article groups.
"""
from typing import Dict, Set, Tuple, List
import numpy as np

from nl_utils.logger_config import get_logger, get_module_name
from nl_utils.file_handler import FileHandler, FileType
from nl_article_processor.text_processor import TextProcessor
from nl_article_processor.similarity_strategies import LSASimilarity


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
        self.similarity_strategy = LSASimilarity(params={'n_components': 100})

        # Initialize article storage
        self.articles = None
        self.articles_dict = None
        self.current_date = None
        self.corpus_fitted = False

    def _prepare_corpus(self, article_groups: Dict) -> None:
        """Prepare and fit the corpus for LSA similarity.

        Args:
            article_groups (Dict): The article groups containing the corpus.
        """
        if self.corpus_fitted and self.current_date == article_groups.get('date'):
            return

        self.logger.info("Preparing corpus for LSA similarity")

        # Load articles if needed
        self._load_articles(article_groups.get('date'))

        # Collect all article lemmas
        corpus = []
        for article in self.articles:
            lemmas = article.get('article_lemmas', [])
            if lemmas:
                corpus.append(' '.join(lemmas))

        if not corpus:
            self.logger.error(
                "No lemmas found in articles for corpus preparation")
            return

        # Set and fit the corpus
        self.similarity_strategy.set_corpus(corpus)
        self.similarity_strategy.fit()
        self.corpus_fitted = True
        self.logger.info("Corpus prepared with %d documents", len(corpus))

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

    def _get_group_lemmas(self, group: Dict) -> Set[str]:
        """Extract all lemmas from articles in a group.

        Args:
            group (Dict): The article group to process.

        Returns:
            Set[str]: Set of lemmas from all articles in the group.
        """
        group_lemmas = set()
        article_ids = group.get('article_ids', [])

        for article_id in article_ids:
            article = self.articles_dict.get(article_id)
            if article:
                article_lemmas = article.get('article_lemmas', [])
                if article_lemmas:
                    group_lemmas.update(article_lemmas)

        return group_lemmas

    def _calculate_group_probabilities(
        self,
        news_item_lemmas: Set[str],
        article_groups: Dict,
        temperature: float = 0.10
    ) -> List[Tuple[str, float]]:
        """Calculate probabilities for each group using softmax.

        Args:
            news_item_lemmas (Set[str]): Lemmas from the news item.
            article_groups (Dict): The article groups to match against.
            temperature (float): Temperature parameter for softmax.

        Returns:
            List[Tuple[str, float]]: List of (group_id, probability) tuples.
        """
        similarities = []
        group_ids = []

        # Get the groups list from the article_groups dictionary
        groups = article_groups.get('groups', [])
        if not isinstance(groups, list):
            self.logger.error(
                "Article groups 'groups' is not a list: %s", type(groups))
            return []

        # Load articles if needed
        self._load_articles(article_groups.get('date'))

        # Calculate similarities for all groups
        for group in groups:
            group_lemmas = self._get_group_lemmas(group)
            if not group_lemmas:
                continue

            similarity = self.similarity_strategy.calculate_similarity(
                news_item_lemmas, group_lemmas)

            group_id = group.get('details', {}).get('group_number')
            if group_id:
                similarities.append(similarity)
                group_ids.append(group_id)

        if not similarities:
            return []

        # Apply softmax to get probabilities
        similarities = np.array(similarities)
        exp_similarities = np.exp(similarities / temperature)
        probabilities = exp_similarities / np.sum(exp_similarities)

        # Sort by probability in descending order
        sorted_indices = np.argsort(probabilities)[::-1]
        # log.debug the loop through the top 10 groups and output the group id and probability
        self.logger.debug("Top 10 groups and their probabilities for news item")
        for i in sorted_indices[:10]:
            self.logger.debug(
                "Group %s has probability %f", group_ids[i], probabilities[i])
        return [(group_ids[i], float(probabilities[i])) for i in sorted_indices]

    def _select_matching_groups(
        self,
        group_probabilities: List[Tuple[str, float]]
    ) -> List[Tuple[str, float]]:
        """Select matching groups based on probability distribution.

        Args:
            group_probabilities (List[Tuple[str, float]]): List of (group_id, probability) tuples.

        Returns:
            List[Tuple[str, float]]: Selected matching groups.
        """
        if not group_probabilities:
            return []

        # Get the highest probability
        max_prob = group_probabilities[0][1]

        # If the highest probability is very high (>0.7), only take that one
        if max_prob > 0.7:
            return [group_probabilities[0]]

        # If the highest probability is moderate (0.4-0.7), take groups that are close to it
        if max_prob > 0.4:
            threshold = max_prob * 0.5  # Take groups with at least 50% of max probability
            return [g for g in group_probabilities if g[1] >= threshold]

        # If the highest probability is low (<0.4), take groups that are significantly above average
        mean_prob = np.mean([p for _, p in group_probabilities])
        std_prob = np.std([p for _, p in group_probabilities])
        threshold = mean_prob + 0.5 * std_prob
        return [g for g in group_probabilities if g[1] >= threshold]

    def match_news_items(self, newsletter: Dict, article_groups: Dict) -> Dict:
        """Match news items with article groups using LSA similarity and softmax probabilities.

        Args:
            newsletter (Dict): The newsletter content.
            article_groups (Dict): The article groups.

        Returns:
            Dict: Newsletter with matched article groups.
        """
        try:
            self.logger.info("Matching news items with article groups")

            # Prepare corpus for LSA similarity
            self._prepare_corpus(article_groups)

            # Create a copy of the newsletter to modify
            matched_newsletter = newsletter.copy()

            # Define categories to match
            categories = [
                '', 'key_events', 'domestic_news', 'foreign_news',
                'business', 'famous_people', 'sports', 'arts', 'science'
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

                    # Calculate probabilities for all groups
                    group_probabilities = self._calculate_group_probabilities(
                        set(lemmas), article_groups)

                    # Select matching groups
                    selected_groups = self._select_matching_groups(
                        group_probabilities)

                    # Add match information
                    matched_newsletter[category][i]['matches'] = [
                        {
                            'group_id': group_id,
                            'probability': prob
                        }
                        for group_id, prob in selected_groups
                    ]

                    self.logger.debug(
                        "Added match info for %s item %d: %d matches",
                        category, i, len(selected_groups))

            return matched_newsletter

        except Exception as e:
            self.logger.error("Error matching news items: %s", str(e))
            return newsletter
