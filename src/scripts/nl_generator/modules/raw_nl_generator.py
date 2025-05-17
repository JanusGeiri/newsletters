#!/usr/bin/env python3
"""
Module for generating raw newsletters using OpenAI.
"""
import json
import os
from pathlib import Path
from typing import Dict, Optional

import tiktoken
from openai import OpenAI
from dotenv import load_dotenv

from nl_utils.logger_config import get_logger, get_module_name
from nl_utils.file_handler import FileHandler, FileType
from nl_utils.newsletter_schemas import DAILY_MORNING_SCHEMA


class RawNLGenerator:
    """Class for generating raw newsletters using OpenAI."""

    def __init__(self, debug_mode: bool = False):
        """Initialize the RawNLGenerator.

        Args:
            debug_mode (bool): Whether to run in debug mode.
        """
        self.logger = get_logger(get_module_name(__name__))
        self.debug_mode = debug_mode
        load_dotenv()
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.file_handler = FileHandler()

    def estimate_tokens(self, text: str, model: str = "gpt-4") -> int:
        """Estimate the number of tokens in a text string.

        Args:
            text (str): The text to estimate tokens for.
            model (str): The model to use for token estimation.

        Returns:
            int: Estimated number of tokens.
        """
        try:
            encoding = tiktoken.encoding_for_model(model)
            return len(encoding.encode(text))
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))

    def generate_newsletter(self, prompt: str) -> Optional[Dict]:
        """Generate a newsletter using the OpenAI API.

        Args:
            prompt (str): The prompt to use for generation.

        Returns:
            Optional[Dict]: The generated newsletter content.
        """
        try:
            self.logger.info("Generating newsletter from prompt")
            prompt_tokens = self.estimate_tokens(prompt)
            self.logger.info("Estimated prompt tokens: %d", prompt_tokens)

            schema = DAILY_MORNING_SCHEMA
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{"role": "system", "content": prompt}],
                response_format={
                    "type": "json_schema",
                    "json_schema": schema.get("json_schema")
                },
                temperature=0.01
            )

            completion_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens
            self.logger.info("Completion tokens: %d", completion_tokens)
            self.logger.info("Total tokens used: %d", total_tokens)

            newsletter_json = json.loads(response.choices[0].message.content)
            return newsletter_json

        except Exception as e:
            self.logger.error("Error generating newsletter: %s", str(e))
            return None

    def save_newsletter(self, newsletter_content: Dict, date_str: str) -> Optional[str]:
        """Save the generated newsletter to a JSON file.

        Args:
            newsletter_content (Dict): The content of the newsletter to save.
            date_str (str): The date string to use in the filename.

        Returns:
            Optional[str]: The path to the saved newsletter file.
        """
        try:
            file_path = self.file_handler.save_file(
                content=newsletter_content,
                file_type=FileType.UNPROCESSED_NEWSLETTER,
                date_str=date_str,
                base_name="newsletter_unprocessed"
            )

            self.logger.info("Saved unprocessed newsletter to: %s", file_path)
            return str(file_path)

        except Exception as e:
            self.logger.error("Error saving newsletter: %s", str(e))
            return None

    def run_generator(self, prompt: str, date_str: str, ignore: bool = False) -> Optional[str]:
        """Run the newsletter generation process.

        Args:
            prompt (str): The prompt to use for generation.
            date_str (str): Date string in YYYY-MM-DD format.
            ignore (bool): Whether to ignore operations.

        Returns:
            Optional[str]: Path to the generated newsletter file.
        """
        if ignore:
            self.logger.info("Ignoring newsletter generation")
            return str(Path("src/outputs/newsletters/unprocessed/dummy.json"))

        try:
            self.logger.info("Starting newsletter generation for %s", date_str)

            # Generate newsletter
            newsletter_content = self.generate_newsletter(prompt)
            if not newsletter_content:
                return None

            # Save newsletter
            return self.save_newsletter(newsletter_content, date_str)

        except Exception as e:
            self.logger.error("Error in newsletter generation: %s", str(e))
            return None
