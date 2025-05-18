"""Agglomerative clustering strategy implementation."""
from typing import Dict, List, Tuple, Any

import numpy as np
from sklearn.cluster import AgglomerativeClustering

from .base_clustering import ClusteringStrategy


class AgglomerativeClusteringStrategy(ClusteringStrategy):
    """Agglomerative clustering implementation."""

    def __init__(self, params: Dict[str, Any]):
        """Initialize Agglomerative clustering strategy.

        Args:
            params (Dict[str, Any]): Dictionary of parameters for the clustering strategy.
                Must contain:
                - n_clusters (int, optional): Number of clusters. If None, distance_threshold is used.
                - distance_threshold (float): Threshold for distance-based clustering.
        """
        super().__init__(params)
        self.n_clusters = self.params.get('n_clusters')
        if self.params.get('distance_threshold') is None:
            self.logger.error(
                "Missing required parameter 'distance_threshold'")
            raise ValueError(
                "Missing required parameter 'distance_threshold'")
        self.distance_threshold = self.params.get('distance_threshold')

    def cluster_articles(
        self,
        articles_lemmas: Dict[str, List[str]],
    ) -> List[List[Tuple[str, List[str]]]]:
        """Cluster articles using Agglomerative clustering.

        Args:
            articles_lemmas (Dict[str, List[str]]): Dictionary mapping article IDs to their lemmas.
            similarity_threshold (float): Minimum similarity score to consider articles similar.

        Returns:
            List[List[Tuple[str, List[str]]]]: List of clusters, where each cluster is a list of
            (article_id, lemmas) tuples.
        """
        # Convert lemmas to sets
        self.logger.info(
            "Starting Agglomerative clustering with parameters: n_clusters=%s, distance_threshold=%s",
            self.n_clusters, self.distance_threshold)
        article_sets = self._convert_to_sets(articles_lemmas)
        article_ids = list(article_sets.keys())

        # Create similarity matrix
        n_articles = len(article_ids)
        similarity_matrix = np.zeros((n_articles, n_articles))

        for i, id1 in enumerate(article_ids):
            for j, id2 in enumerate(article_ids):
                if i != j:
                    similarity = self.similarity_strategy.calculate_similarity(
                        article_sets[id1], article_sets[id2])
                    similarity_matrix[i, j] = similarity

        # Convert similarity to distance
        distance_matrix = 1 - similarity_matrix

        # Apply Agglomerative clustering
        if self.n_clusters is None:
            # Use distance threshold
            clusterer = AgglomerativeClustering(
                n_clusters=None,
                distance_threshold=self.distance_threshold,
                metric='precomputed',
                linkage='average'
            )
        else:
            # Use fixed number of clusters
            clusterer = AgglomerativeClustering(
                n_clusters=self.n_clusters,
                metric='precomputed',
                linkage='average'
            )

        labels = clusterer.fit_predict(distance_matrix)

        # Group articles by cluster
        clusters = {}
        for i, label in enumerate(labels):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(
                (article_ids[i], articles_lemmas[article_ids[i]]))

        # Convert clusters to list format
        return list(clusters.values())
