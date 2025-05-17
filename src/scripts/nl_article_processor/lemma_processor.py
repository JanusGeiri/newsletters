"""Module for processing and filtering article lemmas."""
from collections import defaultdict
from typing import Dict, List

from nl_utils.logger_config import get_logger, get_module_name


class LemmaProcessor:
    """Class for processing and filtering article lemmas."""

    def __init__(self, debug_mode: bool = False):
        """Initialize the LemmaProcessor.

        Args:
            debug_mode (bool): Whether to run in debug mode.
        """
        self.logger = get_logger(get_module_name(__name__))
        self.debug_mode = debug_mode

    def process_articles(self, articles: List[Dict]) -> Dict[str, List[str]]:
        """Process articles to extract and filter lemmas.

        Args:
            articles (List[Dict]): List of articles to process.

        Returns:
            Dict[str, List[str]]: Dictionary mapping article IDs to their filtered lemmas.
        """
        try:
            # Process each article to extract lemmas
            articles_lemmas = {}
            lemma_frequency = defaultdict(int)
            article_count = 0

            # First pass: Process articles and count lemma frequencies
            for idx, article in enumerate(articles, 1):
                article_id = article.get('article_id', f'article_{idx}')
                article_source = article.get('article_source', 'Unknown')
                lemmas = article.get('article_lemmas', [])

                if not lemmas:
                    self.logger.warning(
                        "No lemmas found for article %s from %s", article_id, article_source)
                    continue

                self.logger.debug(
                    "Processing article %d/%d: %s from %s",
                    idx, len(articles), article_id, article_source)

                # Count how many articles each lemma appears in
                for lemma in set(lemmas):
                    lemma_frequency[lemma] += 1

                articles_lemmas[article_id] = lemmas
                article_count += 1

            # Calculate threshold for common lemmas (e.g., appears in more than 20% of articles)
            frequency_threshold = article_count * 0.2
            common_lemmas = {lemma for lemma, freq in lemma_frequency.items()
                             if freq > frequency_threshold}

            self.logger.info(
                "Found %d common lemmas appearing in >%.1f articles",
                len(common_lemmas), frequency_threshold)

            # Second pass: Filter out common lemmas from results
            for article_id in articles_lemmas:
                filtered_lemmas = [lemma for lemma in articles_lemmas[article_id]
                                   if lemma not in common_lemmas]
                articles_lemmas[article_id] = filtered_lemmas

            return articles_lemmas

        except Exception as e:
            self.logger.error("Error processing article lemmas: %s", str(e))
            return {}
