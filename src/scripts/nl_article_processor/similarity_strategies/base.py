"""Base class for similarity strategies."""
from abc import ABC, abstractmethod
from typing import Set


class SimilarityStrategy(ABC):
    """Abstract base class for similarity calculation strategies."""

    @abstractmethod
    def calculate_similarity(self, article1: Set[str], article2: Set[str]) -> float:
        """Calculate similarity between two articles.

        Args:
            article1 (Set[str]): First article's lemmas.
            article2 (Set[str]): Second article's lemmas.

        Returns:
            float: Similarity score between 0 and 1.
        """
