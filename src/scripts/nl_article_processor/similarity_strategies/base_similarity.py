"""Base class for similarity strategies."""
from abc import ABC, abstractmethod
from typing import Set, Dict, Any, List
import os
import json
from datetime import datetime

from nl_utils.logger_config import get_logger, get_module_name


class SimilarityStrategy(ABC):
    """Abstract base class for similarity calculation strategies."""

    def __init__(self, params: Dict[str, Any]):
        """Initialize the similarity strategy.

        Args:
            params (Dict[str, Any]): Parameters for the similarity strategy.
        """
        self.params = params
        self.logger = get_logger(get_module_name(__name__))
        self.corpus = None
        self.similarity_log = []
        self.similarity_log_dir = 'src/outputs/logs/similarity_logs/'
        os.makedirs(self.similarity_log_dir, exist_ok=True)

    def set_corpus(self, corpus: List[List[str]]):
        """Set the corpus for the similarity strategy.

        Args:
            corpus (List[List[str]]): List of lists of lemmas in the corpus.
        """
        self.corpus = corpus

    def log_similarity(self, similarity: float):
        """Log similarity calculation and save to file.

        Args:
            similarity (float): Calculated similarity score.
        """
        log_entry = {
            'similarity': similarity,
        }
        self.similarity_log.append(log_entry)
        self.logger.debug(
            "Similarity between articles: %s",
            similarity
        )

    def save_similarity_log(self):
        """Save the similarity log to a JSON file."""
        if not self.similarity_log:
            self.logger.warning("No similarity calculations to save")
            return

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"similarity_log_{self.__class__.__name__}_{timestamp}.json"
        filepath = 'src/outputs/logs/similarity_logs/' + filename

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.similarity_log, f, ensure_ascii=False, indent=2)
            self.logger.info(
                "Saved similarity log to %s",
                filepath
            )
        except Exception as e:
            self.logger.error(
                "Failed to save similarity log: %s",
                str(e)
            )

    @abstractmethod
    def fit(self):
        """Fit the similarity strategy on the corpus."""

    @abstractmethod
    def calculate_similarity(self, article1: Set[str], article2: Set[str]) -> float:
        """Calculate similarity between two sets of lemmas.

        Args:
            article1 (Set[str]): First set of lemmas.
            article2 (Set[str]): Second set of lemmas.

        Returns:
            float: Similarity score between 0 and 1.
        """
