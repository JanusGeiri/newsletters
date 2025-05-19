#!/usr/bin/env python3
"""
Module for processing text and extracting lemmas from Icelandic text.
"""
import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Set
from reynir import Greynir

from nl_utils.logger_config import get_logger, get_module_name


def load_stopwords() -> Set[str]:
    """Load Icelandic stopwords from JSON file.

    Returns:
        Set[str]: Set of stopwords.
    """
    try:
        # Get the directory of the current file
        current_dir = Path(__file__).parent
        stopwords_file = current_dir / "icelandic_stopwords.json"

        with open(stopwords_file, 'r', encoding='utf-8') as f:
            stopwords_dict = json.load(f)

        # Flatten the dictionary values into a single set
        return {word for words in stopwords_dict.values() for word in words}
    except Exception as e:
        logger = get_logger(get_module_name(__name__))
        logger.error("Error loading stopwords: %s", str(e))
        return set()


# Load stopwords from JSON file
ICELANDIC_STOPWORDS = load_stopwords()


class TextProcessor:
    """Class for processing text and extracting lemmas from Icelandic text."""

    def __init__(self, debug_mode: bool = False):
        """Initialize the TextProcessor.

        Args:
            debug_mode (bool): Whether to run in debug mode.
        """
        self.logger = get_logger(get_module_name(__name__))
        self.debug_mode = debug_mode
        self.greynir = Greynir()

    def clean_html_text(self, text: str) -> str:
        """Remove HTML elements and clean up the text.

        Args:
            text (str): Input text containing HTML elements.

        Returns:
            str: Cleaned text with HTML elements removed.
        """
        try:
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', '', text)

            # Replace HTML entities
            html_entities = {
                '&nbsp;': ' ',
                '&amp;': '&',
                '&lt;': '<',
                '&gt;': '>',
                '&quot;': '"',
                '&apos;': "'",
                '&#x27;': "'",
                '&#39;': "'",
                '&#34;': '"',
            }
            for entity, char in html_entities.items():
                text = text.replace(entity, char)

            # Fix space before period at end of text
            if text.endswith(' .'):
                text = text[:-2] + '.'

            # Fix spaces before commas
            while ' ,' in text:
                text = text.replace(' ,', ',')

            # Remove multiple spaces
            text = re.sub(r'\s+', ' ', text)

            # Remove multiple newlines
            text = re.sub(r'\n+', '\n', text)

            # Strip whitespace from start and end
            return text.strip()

        except Exception as e:
            self.logger.error("Error cleaning HTML: %s", str(e))
            return text

    def process_sentence(self, sent: object, article_source: str = 'Unknown') -> Optional[Dict]:
        """Process a single sentence with error handling.

        Args:
            sent: Sentence object from Greynir.
            article_source (str): Source of the article for logging.

        Returns:
            Optional[Dict]: Processed sentence data or None if processing failed.
        """
        try:
            # Attempt to parse the sentence
            parse_result = sent.parse()
            if not parse_result:
                self.logger.debug(
                    "Failed to parse sentence from %s: %s", article_source, sent.text)
                return None

            # Check if lemmas exist
            if not sent.lemmas:
                self.logger.warning(
                    "No lemmas found for sentence from %s: %s", article_source, sent.text)
                return None

            # Filter and process lemmas
            filtered_lemmas = [
                lemma.lower()
                for lemma in sent.lemmas
                if lemma and lemma.lower() not in ICELANDIC_STOPWORDS
            ]

            return {
                'original': sent.tidy_text,
                'filtered_lemmas': filtered_lemmas,
                'lemma_count': len(filtered_lemmas)
            }

        except Exception as e:
            self.logger.error(
                "Error processing sentence from %s: %s\nFull text: %s",
                article_source, str(e), sent.text)
            return None

    def extract_lemmas(self, text: str, article_source: str = 'Unknown') -> List[str]:
        """Extract unique lemmas from text.

        Args:
            text (str): Input text to process.
            article_source (str): Source of the article for logging.

        Returns:
            List[str]: List of lemmas from the text.
        """
        try:
            # Clean HTML from text
            cleaned_text = self.clean_html_text(text)

            # Submit cleaned text to Greynir
            job = self.greynir.submit(cleaned_text)

            # Process sentences and collect lemmas
            all_lemmas = []
            sentence_count = 0
            successful_parses = 0

            for sent in job:
                sentence_count += 1
                # Clean the individual sentence text again
                sent.text = self.clean_html_text(sent.text)
                result = self.process_sentence(sent, article_source)

                if result:
                    successful_parses += 1
                    all_lemmas.extend(result['filtered_lemmas'])

            self.logger.info(
                "Extracted %d lemmas from %d sentences (%d successful parses)",
                len(all_lemmas), sentence_count, successful_parses)
            return all_lemmas

        except Exception as e:
            self.logger.error(
                "Error extracting lemmas from %s: %s", article_source, str(e))
            return []
