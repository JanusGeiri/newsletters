"""Latent Semantic Analysis (LSA) similarity strategy implementation."""
from typing import Set, Dict, Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics.pairwise import cosine_similarity

from .base_similarity import SimilarityStrategy


class LSASimilarity(SimilarityStrategy):
    """Latent Semantic Analysis (LSA) based similarity."""

    def __init__(self, params: Dict[str, Any]):
        """Initialize LSA similarity strategy.

        Args:
            params (Dict[str, Any]): Parameters for the similarity strategy.
                Must contain:
                - n_components (int): Number of components for LSA.
        """
        super().__init__(params)
        self.n_components = params.get('n_components', 100)
        self.vectorizer = TfidfVectorizer(analyzer='word',)
        self.lsa = TruncatedSVD(n_components=self.n_components)
        # Fit the vectorizer on the corpus

    def fit_vectorizer(self):
        """Fit the vectorizer on the corpus."""
        if self.corpus:
            self.vectorizer.fit(self.corpus)
        else:
            raise ValueError(f'Corpus is empty in {self.__class__.__name__}')

    def fit_lsa(self):
        """Fit the LSA model on the corpus."""
        if self.corpus:
            self.lsa.fit(self.vectorizer.transform(self.corpus))
        else:
            raise ValueError(f'Corpus is empty in {self.__class__.__name__}')

    def fit(self):
        """Fit the similarity strategy on the corpus."""
        self.fit_vectorizer()
        self.fit_lsa()

    def calculate_similarity(self, article1: Set[str], article2: Set[str]) -> float:
        """Calculate LSA-based similarity between two articles.

        Args:
            article1 (Set[str]): First set of lemmas.
            article2 (Set[str]): Second set of lemmas.

        Returns:
            float: LSA similarity score (0-1).
        """
        # Convert sets to strings for vectorization
        article1_str = ' '.join(article1)
        article2_str = ' '.join(article2)

        # Transform articles to TF-IDF vectors
        vec1 = self.vectorizer.transform([article1_str])
        vec2 = self.vectorizer.transform([article2_str])

        # Transform to LSA space
        lsa1 = self.lsa.transform(vec1)
        lsa2 = self.lsa.transform(vec2)

        # Calculate cosine similarity in LSA space
        similarity = cosine_similarity(lsa1, lsa2)[0][0]

        # Log the similarity calculation
        self.log_similarity(similarity)

        return float(similarity)
