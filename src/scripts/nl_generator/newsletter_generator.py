#!/usr/bin/env python3
"""
Newsletter generator module for creating newsletters from news articles.
"""
import argparse
from typing import Optional

from nl_utils.logger_config import get_logger, get_module_name
from nl_utils.file_handler import FileType, FileHandler

from .modules.prompt_generator import PromptGenerator
from .modules.raw_nl_generator import RawNLGenerator
from .modules.nl_processor import NLProcessor


class NewsletterGenerator:
    """Class for generating and processing newsletters."""

    def __init__(self, debug_mode: bool = False):
        """Initialize the NewsletterGenerator.

        Args:
            debug_mode (bool): Whether to run in debug mode.
        """
        self.logger = get_logger(get_module_name(__name__))
        self.debug_mode = debug_mode
        self.file_handler = FileHandler()
        self.prompt_generator = PromptGenerator(debug_mode)
        self.raw_generator = RawNLGenerator(debug_mode)
        self.nl_processor = NLProcessor(debug_mode)

    def run_matching(self, date_str: str, ignore: bool = False) -> Optional[str]:
        """Run only the matching process on an existing newsletter.

        Args:
            date_str (str): Date string in YYYY-MM-DD format.
            ignore (bool): Whether to ignore operations.

        Returns:
            Optional[str]: Path to the processed newsletter file.
        """
        try:
            if ignore:
                self.logger.info("Ignoring matching process")
                return "src/outputs/newsletters/processed/dummy.json"

            self.logger.info("Starting matching process for %s", date_str)

            # Load unprocessed newsletter
            newsletter = self.file_handler.load_file(
                FileType.UNPROCESSED_NEWSLETTER,
                date_str=date_str,
                base_name="newsletter_unprocessed"
            )
            if not newsletter:
                self.logger.error(
                    "No unprocessed newsletter found for date: %s", date_str)
                return None

            # Load article groups
            article_groups = self.file_handler.load_file(
                FileType.ARTICLE_GROUPS,
                date_str=date_str,
                base_name="article_groups"
            )
            if not article_groups:
                self.logger.error(
                    "No article groups found for date: %s", date_str)
                return None

            # Run matching process
            return self.nl_processor.run_matching(newsletter, article_groups, date_str)

        except Exception as e:
            self.logger.error("Error in matching process: %s", str(e))
            return None

    def run_generator(self, date_str: str, ignore: bool = False, ignore_generation: bool = False, ignore_impacts: bool = False, ignore_matching: bool = False) -> Optional[str]:
        """Run the newsletter generation process.

        Args:
            date_str (str): Date string in YYYY-MM-DD format.
            ignore (bool): Whether to ignore operations.
            ignore_generation (bool): Whether to skip generation process.
            ignore_impacts (bool): Whether to skip impact generation and return placeholders.
            ignore_matching (bool): Whether to skip matching process.
        Returns:
            Optional[str]: Path to the generated newsletter file.
        """
        try:
            if ignore:
                self.logger.info("Ignoring newsletter generation")
                return "src/outputs/newsletters/processed/dummy.json"

            self.logger.info("Starting newsletter generation for %s", date_str)

            self.logger.info("Loading article groups data...")
            # Load article groups
            article_groups = self.file_handler.load_file(
                FileType.ARTICLE_GROUPS,
                date_str=date_str,
                base_name="article_groups"
            )
            if not article_groups:
                self.logger.error("✗ Failed to load article groups")
                return None

            # Generate prompt
            prompt = self.prompt_generator.generate_prompt(
                article_groups, date_str)
            if not prompt:
                return None

            # Generate raw newsletter
            raw_newsletter_file = self.raw_generator.run_generator(
                prompt, date_str, ignore_generation)
            if not raw_newsletter_file:
                return None

            # Process newsletter
            final_newsletter_file = self.nl_processor.run_processor(
                date_str, ignore_matching, ignore_impacts)
            if not final_newsletter_file:
                return None

            self.logger.info("Newsletter generation completed successfully")
            return final_newsletter_file

        except Exception as e:
            self.logger.error("Error in newsletter generation: %s", str(e))
            return None


def main():
    """Main function to run the newsletter generator."""
    parser = argparse.ArgumentParser(
        description='Generate newsletters from news articles')
    parser.add_argument(
        '--date', help='Date of the news articles (YYYY-MM-DD)')
    parser.add_argument('--sample-size', type=int, default=200,
                        help='Number of articles to sample')
    parser.add_argument('--add-impacts', action='store_true',
                        help='Add impact analysis to an existing newsletter')
    parser.add_argument('--ignore', action='store_true',
                        help='Ignore operations')
    parser.add_argument('--ignore-impacts', action='store_true',
                        help='Skip impact generation and return placeholders')
    parser.add_argument('--matching-only', action='store_true',
                        help='Run only the matching process')
    args = parser.parse_args()

    try:
        generator = NewsletterGenerator()
        logger = get_logger(get_module_name(__name__))

        if args.matching_only:
            success = generator.run_matching(args.date, args.ignore)
            if success:
                print("Successfully completed matching for %s", args.date)
            else:
                print("Failed to complete matching for %s", args.date)
            return

        if args.add_impacts:
            if not args.date:
                logger.error("Date is required when adding impacts")
                return
            success = generator.nl_processor.run_processor(
                args.date, args.ignore, args.ignore_impacts)
            if success:
                print("Successfully added impacts to newsletter for %s", args.date)
            else:
                print("Failed to add impacts to newsletter for %s", args.date)
            return

        # Load articles
        articles = generator.file_handler.load_file(
            FileType.ARTICLES,
            date_str=args.date,
            base_name="articles"
        )
        if not articles:
            logger.error("Failed to load articles")
            return

        # Load article groups
        article_groups = generator.file_handler.load_file(
            FileType.ARTICLE_GROUPS,
            date_str=args.date,
            base_name="article_groups"
        )
        if not article_groups:
            logger.error("Failed to load article groups")
            return

        output_file = generator.run_generator(
            args.date, args.ignore, args.ignore_impacts)
        if output_file:
            print("Newsletter generated successfully and saved to: %s", output_file)
        else:
            print("Failed to generate newsletter")

    except Exception as e:
        logger.error("Error in newsletter generation: %s", str(e))
        raise


if __name__ == "__main__":
    main()
