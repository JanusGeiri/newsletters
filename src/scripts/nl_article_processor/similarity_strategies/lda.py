"""Latent Dirichlet Allocation (LDA) similarity strategy implementation."""
from typing import Set, Dict, Any

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.metrics.pairwise import cosine_similarity

from .base_similarity import SimilarityStrategy


class LDASimilarity(SimilarityStrategy):
    """Latent Dirichlet Allocation (LDA) based similarity."""

    def __init__(self, params: Dict[str, Any]):
        """Initialize LDA similarity strategy.

        Args:
            params (Dict[str, Any]): Parameters for the similarity strategy.
                Must contain:
                - n_topics (int): Number of topics for LDA.
                - max_iter (int): Maximum number of iterations for LDA.
        """
        super().__init__(params)
        self.n_topics = params.get('n_topics', 10)
        self.max_iter = params.get('max_iter', 10)
        self.vectorizer = CountVectorizer(analyzer=lambda x: x)
        self.lda = LatentDirichletAllocation(
            n_components=self.n_topics,
            max_iter=self.max_iter,
            random_state=42
        )

    def fit_vectorizer(self):
        """Fit the vectorizer on the corpus."""
        if self.corpus:
            self.vectorizer.fit(self.corpus)
        else:
            raise ValueError(f'Corpus is empty in {self.__class__.__name__}')

    def fit_lda(self):
        """Fit the LDA model on the corpus."""
        if self.corpus:
            corpus_matrix = self.vectorizer.transform(self.corpus)
            self.lda.fit(corpus_matrix)
        else:
            raise ValueError(f'Corpus is empty in {self.__class__.__name__}')

    def fit(self):
        """Fit the similarity strategy on the corpus."""
        self.fit_vectorizer()
        self.fit_lda()

    def calculate_similarity(self, article1: Set[str], article2: Set[str]) -> float:
        """Calculate LDA-based similarity between two articles.

        Args:
            article1 (Set[str]): First set of lemmas.
            article2 (Set[str]): Second set of lemmas.

        Returns:
            float: LDA similarity score (0-1).
        """
        # Convert sets to strings for vectorization
        article1_str = ' '.join(article1)
        article2_str = ' '.join(article2)

        # Transform articles to document-term matrices
        vec1 = self.vectorizer.transform([article1_str])
        vec2 = self.vectorizer.transform([article2_str])

        # Transform to topic distributions
        topic_dist1 = self.lda.transform(vec1)
        topic_dist2 = self.lda.transform(vec2)

        # Calculate cosine similarity between topic distributions
        similarity = cosine_similarity(topic_dist1, topic_dist2)[0][0]

        # Log the similarity calculation
        self.log_similarity(similarity)

        return float(similarity)
