#!/usr/bin/env python3
"""
Module for processing news articles into article groups.
"""
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from nl_utils.logger_config import get_logger, get_module_name
from nl_utils.file_handler import FileHandler, FileType
from .similarity_strategies import (
    SimilarityStrategy,
    JaccardSimilarity,
    EnhancedJaccardSimilarity,
    LSASimilarity
)
from .lemma_processor import LemmaProcessor


class ArticleGroupProcessor:
    """Class for processing news articles into article groups."""

    def __init__(self, similarity_strategy: SimilarityStrategy, debug_mode: bool = False):
        """Initialize the ArticleGroupProcessor.

        Args:
            similarity_strategy (SimilarityStrategy): Strategy for calculating article similarity.
            debug_mode (bool): Whether to run in debug mode.
        """
        self.logger = get_logger(get_module_name(__name__))
        self.debug_mode = debug_mode
        self.file_handler = FileHandler()
        self.similarity_strategy = similarity_strategy
        self.lemma_processor = LemmaProcessor(debug_mode=debug_mode)

    def find_similar_articles(
        self,
        articles_lemmas: Dict[str, List[str]],
        similarity_threshold: float = 0.3
    ) -> List[List[Tuple[str, List[str]]]]:
        """Group articles based on lemma similarity.

        Args:
            articles_lemmas (Dict[str, List[str]]): Dictionary mapping article IDs to their lemmas.
            similarity_threshold (float): Minimum similarity score to consider articles similar.

        Returns:
            List[List[Tuple[str, List[str]]]]: List of groups, where each group is a list of
            (article_id, lemmas) tuples.
        """
        try:
            # Convert lemma lists to sets for faster comparison
            article_sets = {
                article_id: set(lemmas)
                for article_id, lemmas in articles_lemmas.items()
            }

            # Initialize groups
            groups = []
            processed_articles = set()

            for article_id, lemma_set in article_sets.items():
                # Skip if article already processed
                if article_id in processed_articles:
                    continue

                # Start a new group with current article
                current_group = [(article_id, articles_lemmas[article_id])]
                processed_articles.add(article_id)

                # Find similar articles
                for other_id, other_lemmas in article_sets.items():
                    if other_id != article_id and other_id not in processed_articles:
                        similarity = self.similarity_strategy.calculate_similarity(
                            lemma_set, other_lemmas)

                        if similarity >= similarity_threshold:
                            current_group.append(
                                (other_id, articles_lemmas[other_id]))
                            processed_articles.add(other_id)

                groups.append(current_group)

            # Sort groups by size (largest first)
            groups.sort(key=len, reverse=True)
            return groups

        except Exception as e:
            self.logger.error("Error grouping similar articles: %s", str(e))
            return []

    def process_articles(self, articles: List[Dict], date_str: str) -> Optional[Dict]:
        """Process articles into article groups.

        Args:
            articles (List[Dict]): List of articles to process.
            date_str (str): Date string in YYYY-MM-DD format.

        Returns:
            Optional[Dict]: Processed article groups.
        """
        try:
            self.logger.info(
                "Processing %d articles into groups", len(articles))

            # Process articles to get filtered lemmas
            articles_lemmas = self.lemma_processor.process_articles(articles)

            # Group similar articles
            groups = self.find_similar_articles(articles_lemmas)

            # Prepare the final output structure
            article_groups = {
                "date": date_str,
                "groups": []
            }

            # Convert groups to the required format
            for group in groups:
                group_hash = hashlib.sha256(
                    str(group).encode()).hexdigest()[:8]
                group_data = {
                    "urls": [],
                    "article_ids": [],
                    "details": {
                        "group_number": group_hash,
                        "article_count": len(group),
                        "articles": []
                    }
                }

                # Process each article in the group
                for article_id, lemmas in group:
                    article = next(
                        (a for a in articles if a.get('article_id') == article_id), None)
                    if article:
                        # Add URL to the URLs list
                        group_data["urls"].append(
                            article.get('article_url', 'No URL'))
                        group_data["article_ids"].append(
                            article.get('article_id', 'No ID'))
                        # Add detailed article info
                        article_info = {
                            "id": article.get('article_id', 'No ID'),
                            "source": article.get('article_source', 'Unknown'),
                            "title": article.get('article_title', 'No title'),
                            "url": article.get('article_url', 'No URL'),
                            "lemma_count": len(lemmas),
                            "description": article.get('article_description', 'No description'),
                        }
                        group_data["details"]["articles"].append(article_info)

                article_groups["groups"].append(group_data)

            return article_groups

        except Exception as e:
            self.logger.error("Error processing articles: %s", str(e))
            return None

    def save_article_groups(self, article_groups: Dict, date_str: str) -> Optional[Path]:
        """Save processed article groups to a JSON file.

        Args:
            article_groups (Dict): Article groups to save.
            date_str (str): Date string in YYYY-MM-DD format.

        Returns:
            Optional[Path]: Path to saved file if successful, None otherwise.
        """
        try:
            output_path = self.file_handler.save_file(
                article_groups,
                FileType.ARTICLE_GROUPS,
                date_str=date_str,
                base_name="article_groups"
            )

            self.logger.info("Saved article groups to: %s", output_path)
            return output_path

        except Exception as e:
            self.logger.error("Error saving article groups: %s", str(e))
            return None

    def run_processor(self, date_str: str, ignore: bool = False) -> Optional[Path]:
        """Run the article group processing.

        Args:
            date_str (str): Date string in YYYY-MM-DD format.
            ignore (bool): Whether to ignore operations.

        Returns:
            Optional[Path]: Path to saved file if successful, None otherwise.
        """
        if ignore:
            self.logger.info("Ignoring article group processing")
            return Path("src/outputs/news/article_groups/dummy.json")

        try:
            # Load articles
            articles = self.file_handler.load_file(
                FileType.ARTICLES,
                date_str=date_str,
                base_name="articles"
            )
            if not articles:
                self.logger.error(
                    "No articles file found for date: %s", date_str)
                return None

            # Process articles
            article_groups = self.process_articles(articles, date_str)
            if not article_groups:
                return None

            # Save article groups
            return self.save_article_groups(article_groups, date_str)

        except Exception as e:
            self.logger.error("Error in article group processing: %s", str(e))
            return None


def main():
    """Main function to demonstrate usage of different similarity strategies."""
    import argparse
    from datetime import datetime

    parser = argparse.ArgumentParser(
        description='Process articles into groups using different similarity strategies.')
    parser.add_argument('--date', type=str, help='Date in YYYY-MM-DD format',
                        default=datetime.now().strftime('%Y-%m-%d'))
    parser.add_argument('--strategy', type=str, choices=['jaccard', 'enhanced_jaccard', 'lsa'],
                        default='jaccard', help='Similarity strategy to use')
    parser.add_argument('--threshold', type=float,
                        default=0.3, help='Similarity threshold')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug mode')

    args = parser.parse_args()

    # Load articles first to initialize strategies that need all articles
    file_handler = FileHandler()
    articles = file_handler.load_file(
        FileType.ARTICLES,
        date_str=args.date,
        base_name="articles"
    )

    if not articles:
        print(f"No articles found for date: {args.date}")
        return

    # Extract all article lemmas for strategies that need them
    all_articles_lemmas = [set(article.get('lemmas', []))
                           for article in articles]

    # Initialize appropriate strategy
    if args.strategy == 'jaccard':
        strategy = JaccardSimilarity()
    elif args.strategy == 'enhanced_jaccard':
        strategy = EnhancedJaccardSimilarity(all_articles_lemmas)
    else:  # lsa
        strategy = LSASimilarity(all_articles_lemmas)

    # Create processor with chosen strategy
    processor = ArticleGroupProcessor(strategy, debug_mode=args.debug)

    # Run processing
    output_path = processor.run_processor(args.date)

    if output_path:
        print(
            f"Successfully processed articles. Output saved to: {output_path}")
    else:
        print("Failed to process articles.")


if __name__ == "__main__":
    main()
