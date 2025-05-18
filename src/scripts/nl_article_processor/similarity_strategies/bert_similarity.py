"""Sentence-BERT similarity strategy implementation."""
from typing import Set, Dict, Any

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from .base_similarity import SimilarityStrategy


class BERTSimilarity(SimilarityStrategy):
    """Sentence-BERT based similarity."""

    def __init__(self, params: Dict[str, Any]):
        """Initialize BERT similarity strategy.

        Args:
            params (Dict[str, Any]): Parameters for the similarity strategy.
                Must contain:
                - model_name (str): Name of the Sentence-BERT model to use.
                - device (str): Device to run the model on ('cpu' or 'cuda').
        """
        super().__init__(params)
        self.model_name = params.get('model_name', 'all-MiniLM-L6-v2')
        self.device = params.get('device', 'cpu')
        self.model = SentenceTransformer(self.model_name, device=self.device)

    def fit(self):
        """Fit the similarity strategy on the corpus.

        Note: BERT models are pre-trained, so no fitting is needed.
        """

    def calculate_similarity(self, article1: Set[str], article2: Set[str]) -> float:
        """Calculate BERT-based similarity between two articles.

        Args:
            article1 (Set[str]): First set of lemmas.
            article2 (Set[str]): Second set of lemmas.

        Returns:
            float: BERT similarity score (0-1).
        """
        # Convert sets to strings for embedding
        article1_str = ' '.join(article1)
        article2_str = ' '.join(article2)

        # Get embeddings for both articles
        embedding1 = self.model.encode([article1_str])[0]
        embedding2 = self.model.encode([article2_str])[0]

        # Calculate cosine similarity between embeddings
        similarity = cosine_similarity(
            embedding1.reshape(1, -1),
            embedding2.reshape(1, -1)
        )[0][0]

        # Log the similarity calculation
        self.log_similarity(float(similarity))

        return float(similarity)
