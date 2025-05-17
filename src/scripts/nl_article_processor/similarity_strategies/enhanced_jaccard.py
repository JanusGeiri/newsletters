"""Enhanced Jaccard similarity strategy implementation."""
from typing import List, Set

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .base import SimilarityStrategy


class EnhancedJaccardSimilarity(SimilarityStrategy):
    """Enhanced Jaccard similarity with TF-IDF weighting."""

    def __init__(self, all_articles: List[Set[str]]):
        """Initialize with all articles for TF-IDF calculation.

        Args:
            all_articles (List[Set[str]]): List of all article lemma sets.
        """
        self.vectorizer = TfidfVectorizer(analyzer=lambda x: x)
        self.tfidf_matrix = self.vectorizer.fit_transform(
            [' '.join(article) for article in all_articles])

    def calculate_similarity(self, article1: Set[str], article2: Set[str]) -> float:
        """Calculate enhanced Jaccard similarity with TF-IDF weighting.

        Args:
            article1 (Set[str]): First set of lemmas.
            article2 (Set[str]): Second set of lemmas.

        Returns:
            float: Enhanced Jaccard similarity score (0-1).
        """
        # Convert sets to strings for vectorization
        article1_str = ' '.join(article1)
        article2_str = ' '.join(article2)

        # Transform articles to TF-IDF vectors
        vec1 = self.vectorizer.transform([article1_str])
        vec2 = self.vectorizer.transform([article2_str])

        # Calculate cosine similarity
        similarity = cosine_similarity(vec1, vec2)[0][0]
        return float(similarity)
