"""Latent Semantic Analysis (LSA) similarity strategy implementation."""
from typing import List, Set

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics.pairwise import cosine_similarity

from .base import SimilarityStrategy


class LSASimilarity(SimilarityStrategy):
    """Latent Semantic Analysis (LSA) based similarity."""

    def __init__(self, all_articles: List[Set[str]], n_components: int = 100):
        """Initialize LSA with all articles.

        Args:
            all_articles (List[Set[str]]): List of all article lemma sets.
            n_components (int): Number of components for LSA.
        """
        self.vectorizer = TfidfVectorizer(analyzer=lambda x: x)
        self.lsa = TruncatedSVD(n_components=n_components)

        # Fit and transform the data
        tfidf_matrix = self.vectorizer.fit_transform(
            [' '.join(article) for article in all_articles])
        self.lsa_matrix = self.lsa.fit_transform(tfidf_matrix)

    def calculate_similarity(self, article1: Set[str], article2: Set[str]) -> float:
        """Calculate LSA-based similarity between two articles.

        Args:
            article1 (Set[str]): First set of lemmas.
            article2 (Set[str]): Second set of lemmas.

        Returns:
            float: LSA similarity score (0-1).
        """
        # Transform articles to LSA space
        article1_str = ' '.join(article1)
        article2_str = ' '.join(article2)

        vec1 = self.vectorizer.transform([article1_str])
        vec2 = self.vectorizer.transform([article2_str])

        lsa1 = self.lsa.transform(vec1)
        lsa2 = self.lsa.transform(vec2)

        # Calculate cosine similarity in LSA space
        similarity = cosine_similarity(lsa1, lsa2)[0][0]
        return float(similarity)
