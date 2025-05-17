"""Jaccard similarity strategy implementation."""
from typing import Set

from .base import SimilarityStrategy


class JaccardSimilarity(SimilarityStrategy):
    """Jaccard similarity implementation."""

    def calculate_similarity(self, article1: Set[str], article2: Set[str]) -> float:
        """Calculate Jaccard similarity between two sets of lemmas.

        Args:
            article1 (Set[str]): First set of lemmas.
            article2 (Set[str]): Second set of lemmas.

        Returns:
            float: Jaccard similarity score (0-1).
        """
        intersection = len(article1.intersection(article2))
        union = len(article1.union(article2))
        return intersection / union if union > 0 else 0
