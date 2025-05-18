"""Similarity strategies package."""

from .base_similarity import SimilarityStrategy
from .jaccard import JaccardSimilarity
from .lsa import LSASimilarity
from .enhanced_jaccard import EnhancedJaccardSimilarity
from .lda import LDASimilarity
from .bert_similarity import BERTSimilarity

__all__ = [
    'SimilarityStrategy',
    'JaccardSimilarity',
    'LSASimilarity',
    'EnhancedJaccardSimilarity',
    'LDASimilarity',
    'BERTSimilarity'
]
