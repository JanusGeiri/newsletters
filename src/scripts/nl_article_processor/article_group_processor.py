#!/usr/bin/env python3
"""
Module for processing news articles into article groups.
"""
import hashlib
import os
from pathlib import Path
from typing import List, Dict, Optional, Any

from openai import OpenAI
from dotenv import load_dotenv

from nl_utils.logger_config import get_logger, get_module_name
from nl_utils.file_handler import FileHandler, FileType
from .clustering_strategies import ClusteringStrategy
from .similarity_strategies import SimilarityStrategy


def create_group_name(article_titles: List[str], article_descriptions: List[str], prompt_template: str) -> str:
    """Create a concise title for a group of related articles using OpenAI.

    Args:
        article_titles (List[str]): List of article titles in the group
        article_descriptions (List[str]): List of article descriptions in the group

    Returns:
        str: A concise title in Icelandic describing the main story
    """
    try:
        # Load environment variables and initialize OpenAI client
        load_dotenv()
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        # Format article titles and descriptions
        titles_text = "\n".join(
            [f"- {title}" for title in article_titles if title])
        descriptions_text = "\n".join(
            [f"- {desc}" for desc in article_descriptions if desc])

        # Format the prompt
        prompt = prompt_template.format(
            article_titles=titles_text,
            article_descriptions=descriptions_text
        )

        # Generate the group name using OpenAI
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[{"role": "system", "content": prompt}],
            temperature=0.1,
            max_tokens=50
        )

        # Extract and clean the response
        group_name = response.choices[0].message.content.strip()
        return group_name

    except Exception as e:
        logger = get_logger(get_module_name(__name__))
        logger.error("Error creating group name: %s", str(e))
        # Return a fallback name if generation fails
        return "Fréttir um sömu atburði"


class ArticleGroupProcessor:
    """Class for processing news articles into article groups."""

    def __init__(self, params: Dict[str, Any], debug_mode: bool = False):
        """Initialize the ArticleGroupProcessor.

        Args:
            params (Dict[str, Any]): Parameters for the article group processor.
                Must contain:
                - clustering_strategy (ClusteringStrategy): Strategy for clustering articles.
                - similarity_strategy (SimilarityStrategy): Strategy for calculating article similarity.
            debug_mode (bool): Whether to run in debug mode.
        """
        self.logger = get_logger(get_module_name(__name__))
        self.debug_mode = debug_mode
        self.file_handler: FileHandler = FileHandler()
        self.clustering_strategy: ClusteringStrategy = params['clustering_strategy']
        self.similarity_strategy: SimilarityStrategy = params['similarity_strategy']

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

            # Extract lemmas from articles
            articles_lemmas = {
                article['article_id']: article['article_lemmas']
                for article in articles
            }
            articles_corpus = [' '.join(list(article_lemmas))
                               for article_lemmas in articles_lemmas.values()]
            # print(articles_corpus)
            self.similarity_strategy.set_corpus(articles_corpus)
            self.similarity_strategy.fit()

            # Cluster similar articles
            groups = self.clustering_strategy.cluster_articles(
                articles_lemmas
            )
            self.clustering_strategy.log_stats_after_clustering(groups)

            # Prepare the final output structure
            article_groups = {
                "date": date_str,
                "groups": []
            }
            # Load the prompt template
            prompt_template = self.file_handler.load_file(
                FileType.PROMPT,
                base_name="group_name_prompt"
            )

            # Convert groups to the required format
            for group in groups:
                group_hash = hashlib.sha256(
                    str(group).encode()).hexdigest()[:8]
                group_data = {
                    "urls": [],
                    "article_ids": [],
                    "details": {
                        "group_number": group_hash,
                        "group_name": "Title missing",
                        "article_count": len(group),
                        "articles": []
                    }
                }

                # Process each article in the group
                article_titles = []
                article_descriptions = []
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
                        article_titles.append(
                            article.get('article_title', None))
                        article_descriptions.append(
                            article.get('article_description', None))
                        group_data["details"]["articles"].append(article_info)
                group_name = create_group_name(
                    article_titles, article_descriptions, prompt_template)
                group_data["details"]["group_name"] = group_name

                article_groups["groups"].append(group_data)

            # Sort groups by article count in descending order
            article_groups["groups"].sort(
                key=lambda x: x["details"]["article_count"], reverse=True)

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
