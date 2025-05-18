"""Base class for clustering strategies."""
from abc import ABC, abstractmethod
from typing import Dict, List, Set, Tuple, Any

from nl_utils.logger_config import get_logger


class ClusteringStrategy(ABC):
    """Abstract base class for clustering strategies."""

    def __init__(self, params: Dict[str, Any]):
        """Initialize the clustering strategy.

        Args:
            params (Dict[str, Any]): Dictionary of parameters for the clustering strategy.
                Must contain:
                - similarity_strategy (SimilarityStrategy): Strategy for calculating article similarity.
        """
        self.params = params
        self.logger = get_logger(
            f'clustering_strategy_{self.__class__.__name__}')
        self.similarity_strategy = params['similarity_strategy']
        self.similarity_params = params['similarity_params']

    @abstractmethod
    def cluster_articles(
        self,
        articles_lemmas: Dict[str, List[str]],
    ) -> List[List[Tuple[str, List[str]]]]:
        """Cluster articles based on lemma similarity.

        Args:
            articles_lemmas (Dict[str, List[str]]): Dictionary mapping article IDs to their lemmas.

        Returns:
            List[List[Tuple[str, List[str]]]]: List of clusters, where each cluster is a list of
            (article_id, lemmas) tuples.
        """

    def log_stats_after_clustering(self, clusters: List[List[Tuple[str, List[str]]]]):
        """Log out the distribution of clusters by size."""
        # Count clusters of each size
        size_distribution = {}
        for cluster in clusters:
            size = len(cluster)
            size_distribution[size] = size_distribution.get(size, 0) + 1

        # Log the distribution
        self.logger.info("Starting cluster distribution:")
        for size, count in sorted(size_distribution.items()):
            self.logger.info(
                "Number of clusters with size %d: %d",
                size, count)

    def _convert_to_sets(self, articles_lemmas: Dict[str, List[str]]) -> Dict[str, Set[str]]:
        """Convert lemma lists to sets for faster comparison.

        Args:
            articles_lemmas (Dict[str, List[str]]): Dictionary mapping article IDs to their lemmas.

        Returns:
            Dict[str, Set[str]]: Dictionary mapping article IDs to their lemma sets.
        """
        return {
            article_id: set(lemmas)
            for article_id, lemmas in articles_lemmas.items()
        }
