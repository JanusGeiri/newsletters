"""HDBSCAN clustering strategy implementation."""
from typing import Dict, List, Tuple, Any

import numpy as np
from hdbscan import HDBSCAN

from .base_clustering import ClusteringStrategy
from ..similarity_strategies import SimilarityStrategy


class HDBSCANClustering(ClusteringStrategy):
    """HDBSCAN clustering implementation."""

    def __init__(self, params: Dict[str, Any]):
        """Initialize HDBSCAN clustering strategy.

        Args:
            params (Dict[str, Any]): Dictionary of parameters for the clustering strategy.
                Must contain:
                - similarity_strategy (SimilarityStrategy): Strategy for calculating article similarity.
                - similarity_params (Dict[str, Any]): Parameters for the similarity strategy.
                Optional:
                - min_cluster_size (int): Minimum size of clusters. Defaults to 2.
                - min_samples (int): Number of samples in neighborhood for core points. Defaults to 2.

        Raises:
            ValueError: If required parameters are missing.
        """
        super().__init__(params)

        # Validate required parameters
        if 'similarity_strategy' not in self.params:
            self.logger.error(
                "Missing required parameter 'similarity_strategy'")
            raise ValueError(
                "Missing required parameter 'similarity_strategy'")

        # Set parameters with defaults
        self.min_cluster_size = self.params.get('min_cluster_size', 2)
        self.min_samples = self.params.get('min_samples', 2)
        self.similarity_strategy: SimilarityStrategy = self.params['similarity_strategy']

        self.logger.info(
            "Initialized HDBSCAN clustering with min_cluster_size=%d, min_samples=%d",
            self.min_cluster_size, self.min_samples)

    def cluster_articles(
        self,
        articles_lemmas: Dict[str, List[str]],
    ) -> List[List[Tuple[str, List[str]]]]:
        """Cluster articles using HDBSCAN.

        Args:
            articles_lemmas (Dict[str, List[str]]): Dictionary mapping article IDs to their lemmas.

        Returns:
            List[List[Tuple[str, List[str]]]]: List of clusters, where each cluster is a list of
            (article_id, lemmas) tuples. Noise points are treated as individual clusters.

        Raises:
            ValueError: If articles_lemmas is empty or invalid.
        """
        if not articles_lemmas:
            self.logger.error("No articles provided for clustering")
            raise ValueError("No articles provided for clustering")

        try:
            # Convert lemmas to sets
            article_sets = self._convert_to_sets(articles_lemmas)
            article_ids = list(article_sets.keys())
            n_articles = len(article_ids)

            self.logger.info("Clustering %d articles", n_articles)

            # Create similarity matrix
            similarity_matrix = np.zeros((n_articles, n_articles))

            for i, id1 in enumerate(article_ids):
                for j, id2 in enumerate(article_ids):
                    if i != j:
                        similarity = self.similarity_strategy.calculate_similarity(
                            article_sets[id1], article_sets[id2])
                        similarity_matrix[i, j] = similarity

            # Convert similarity to distance (HDBSCAN expects distances)
            distance_matrix = 1 - similarity_matrix

            # Apply HDBSCAN
            clusterer = HDBSCAN(
                min_cluster_size=self.min_cluster_size,
                min_samples=self.min_samples,
                metric='precomputed'
            )
            labels = clusterer.fit_predict(distance_matrix)

            # Group articles by cluster
            clusters = {}
            noise_points = []

            # First, process noise points (label = -1)
            for i, label in enumerate(labels):
                if label == -1:
                    noise_points.append(
                        (article_ids[i], articles_lemmas[article_ids[i]]))
                else:
                    if label not in clusters:
                        clusters[label] = []
                    clusters[label].append(
                        (article_ids[i], articles_lemmas[article_ids[i]]))

            # Add noise points as individual clusters
            for noise_point in noise_points:
                clusters[f"noise_{len(clusters)}"] = [noise_point]

            self.logger.info(
                "Clustering complete: %d multi-article clusters, %d single-article clusters",
                len([c for c in clusters.values() if len(c) > 1]),
                len([c for c in clusters.values() if len(c) == 1]))

            # Convert clusters to list format
            return list(clusters.values())

        except Exception as e:
            self.logger.error("Error during clustering: %s", str(e))
            raise
