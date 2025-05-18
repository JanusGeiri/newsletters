"""Enhanced Jaccard similarity strategy implementation."""
from typing import Set, Dict, Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .base_similarity import SimilarityStrategy


class EnhancedJaccardSimilarity(SimilarityStrategy):
    """Enhanced Jaccard similarity with TF-IDF weighting."""

    def __init__(self, params: Dict[str, Any]):
        """Initialize the enhanced Jaccard similarity strategy.

        Args:
            params (Dict[str, Any]): Parameters for the similarity strategy.
        """
        super().__init__(params)
        self.vectorizer = TfidfVectorizer(analyzer='word')

    def fit(self):
        """Fit the similarity strategy on the corpus."""
        if self.corpus:
            self.vectorizer.fit(self.corpus)
        else:
            raise ValueError('Corpus is empty')

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

        # Log the similarity calculation
        self.log_similarity(similarity)

        return float(similarity)
