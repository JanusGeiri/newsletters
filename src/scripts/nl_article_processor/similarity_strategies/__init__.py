"""Similarity strategies for article grouping."""

from .base import SimilarityStrategy
from .jaccard import JaccardSimilarity
from .enhanced_jaccard import EnhancedJaccardSimilarity
from .lsa import LSASimilarity

__all__ = [
    'SimilarityStrategy',
    'JaccardSimilarity',
    'EnhancedJaccardSimilarity',
    'LSASimilarity',
]
