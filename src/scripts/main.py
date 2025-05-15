#!/usr/bin/env python3
import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
import logging
from enum import Enum
import json
import os
from dotenv import load_dotenv
from nl_utils.logger_config import get_logger, setup_logger

from nl_sender.process_unsubscribes import SubscriberManager
from nl_generator.newsletter_generator import NewsletterGenerator
from nl_scraper.master_scraper import MasterScraper
from nl_formatter.newsletter_formatter import NewsletterFormatter
from nl_formatter.update_index import NewsletterIndexUpdater
from nl_sender.send_newsletter import NewsletterSender
from openai import OpenAI

# Get logger
logger = get_logger('main')

# Load environment variables
load_dotenv()


class RunMode(Enum):
    """Different modes of operation for the newsletter system."""
    SCRAPE_ONLY = "scrape_only"
    GENERATE_ONLY = "generate_only"
    FORMAT_ONLY = "format_only"
    FULL_PIPELINE = "full_pipeline"
    # New mode for generation and formatting without scraping
    GENERATE_AND_FORMAT = "generate_and_format"
    CLEAN_URLS = "clean_urls"


def parse_date(date_str: Optional[str]) -> str:
    """Parse and validate date string.

    Args:
        date_str (Optional[str]): Date string in YYYY-MM-DD format.

    Returns:
        str: Validated date string.
    """
    if not date_str:
        return datetime.now().strftime('%Y-%m-%d')

    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return date_str
    except ValueError:
        raise ValueError("Date must be in YYYY-MM-DD format")


def run_scraper(args) -> None:
    """Run the news scraper.

    Args:
        args: Command line arguments.
    """
    try:
        logger.info("Starting news scraper")

        # Get today's date
        today = datetime.now().date()
        if args.date:
            today = datetime.strptime(args.date, '%Y-%m-%d').date()

        # Initialize master scraper
        master_scraper = MasterScraper(debug_mode=args.verbose)

        # Run the scraper
        output_file = master_scraper.run_scraper(
            date=today,
            sources=args.sources
        )

        if output_file:
            logger.info("Successfully saved articles to: %s", output_file)
        else:
            logger.error("Failed to save articles")

    except Exception as e:
        logger.error("Error in news scraper: %s", str(e))
        raise


def run_impacts(args) -> None:
    """Run the impact insertion process.

    Args:
        args: Command line arguments.
    """
    try:
        logger.info("Starting impact insertion")
        generator = NewsletterGenerator(debug_mode=args.verbose)
        success = generator.run_impacts(args.date, args.ignore)
        if success:
            logger.info("Successfully inserted impacts")
        else:
            logger.error("Failed to insert impacts")

    except Exception as e:
        logger.error("Error in impact insertion: %s", str(e))
        raise


def run_generator(args) -> None:
    """Run the newsletter generator.

    Args:
        args: Command line arguments.
    """
    logger.info("Starting newsletter generation...")

    try:
        # Initialize master scraper
        master_scraper = MasterScraper(debug_mode=args.verbose)

        # Run the scraper
        output_file = master_scraper.run_scraper(
            date=datetime.strptime(args.date, '%Y-%m-%d'),
            sources=args.sources,
            ignore=args.ignore
        )

        if not output_file:
            logger.error("Failed to scrape articles")
            return

        # Initialize newsletter generator
        generator = NewsletterGenerator(debug_mode=args.verbose)
        articles, date_str = generator.load_news_data(
            args.date, args.sample_size)
        if not articles or not date_str:
            logger.error("Failed to load news data")
            return

        output_file = generator.run_generator(date_str, articles, args.ignore)
        if output_file:
            logger.info(
                "Newsletter generated successfully and saved to: %s", output_file)
        else:
            logger.error("Failed to generate newsletter")

    except Exception as e:
        logger.error("Error in newsletter generation: %s", str(e))
        raise


def run_formatter(args) -> None:
    """Run the newsletter formatter.

    Args:
        args: Command line arguments.
    """
    logger.info("Starting newsletter formatting...")

    try:
        # Initialize the formatter
        formatter = NewsletterFormatter()

        # Format the newsletter
        output_file = formatter.format_newsletter(
            date_str=args.date,
            file_path=None,  # Let it find the most recent file
            ignore=args.ignore
        )

        if output_file:
            logger.info("Formatted newsletter saved to: %s", output_file)
        else:
            logger.error("Failed to save formatted newsletter")

    except Exception as e:
        logger.error("Error formatting newsletter: %s", str(e))
        raise


def run_url_cleaner(args) -> None:
    """Run the URL cleaning process.

    Args:
        args: Command line arguments.
    """
    try:
        logger.info("Starting URL cleaning process")
        generator = NewsletterGenerator(debug_mode=args.verbose)
        success = generator.run_url_cleaner(args.date, args.ignore)
        if success:
            logger.info("Successfully cleaned URLs")
        else:
            logger.error("Failed to clean URLs")

    except Exception as e:
        logger.error("Error in URL cleaning process: %s", str(e))
        raise


def run_index_updater(args) -> None:
    """Run the newsletter index updater.

    Args:
        args: Command line arguments.
    """
    logger.info("Starting index update...")

    try:
        # Initialize the index updater
        index_updater = NewsletterIndexUpdater()

        # Update the index
        index_updater.update_index(ignore=args.ignore)

        logger.info("Index update completed successfully")

    except Exception as e:
        logger.error("Error updating index: %s", str(e))
        raise


def run_sender(args) -> None:
    """Run the newsletter sender.

    Args:
        args: Command line arguments.
    """
    logger.info("Starting newsletter sending...")

    try:
        # Initialize the sender
        sender = NewsletterSender(dev_mode=args.dev_mode)

        # Send the newsletter
        sender.send_newsletter(
            date=args.date,
            ignore=args.ignore
        )

        logger.info("Newsletter sending completed successfully")

    except Exception as e:
        logger.error("Error sending newsletter: %s", str(e))
        raise


def run_subscriber_manager(args) -> None:
    """Run the subscriber manager.

    Args:
        args: Command line arguments.
    """
    logger.info("Starting subscriber management...")

    try:
        # Initialize the subscriber manager
        manager = SubscriberManager(debug_mode=args.verbose)

        # Process unsubscribes
        manager.process_unsubscribes(ignore=args.ignore)

        logger.info("Subscriber management completed successfully")

    except Exception as e:
        logger.error("Error in subscriber management: %s", str(e))
        raise


def main():
    """Main function to run the newsletter pipeline."""
    logger = setup_logger(name='main.py main file run',
                          log_file_base='main_py')
    try:
        logger.info("Starting newsletter pipeline")

        # Parse command line arguments
        parser = argparse.ArgumentParser(
            description='Run the newsletter pipeline')
        parser.add_argument('--mode', choices=['scraper', 'generator', 'formatter', 'impacts', 'clean_urls', 'full_pipeline', 'index_updater', 'sender', 'subscriber_manager'],
                            default='full_pipeline', help='Pipeline mode to run')
        parser.add_argument('--date', help='Date to process (YYYY-MM-DD)')
        parser.add_argument('--verbose', action='store_true',
                            help='Enable verbose output')
        parser.add_argument('--sources', nargs='+', default=['visir', 'mbl', 'vb', 'ruv'],
                            help='News sources to process')
        parser.add_argument('--sample_size', type=int, default=200,
                            help='Number of articles to sample')
        parser.add_argument('--dev_mode', action='store_true',
                            help='Enable development mode')
        parser.add_argument('--ignore', action='store_true',
                            help='Ignore operations')
        args = parser.parse_args()

        logger.debug(f"Running with arguments: {args}")

        # Set date to yesterday if not provided
        if not args.date:
            yesterday = datetime.now().date()
            args.date = yesterday.strftime('%Y-%m-%d')
            logger.debug(f"Using date: {args.date}")

        # Run the pipeline
        if args.mode in ['scraper', 'full_pipeline']:
            run_scraper(args)

        if args.mode in ['generator', 'full_pipeline']:
            run_generator(args)

        if args.mode in ['impacts', 'full_pipeline']:
            run_impacts(args)

        if args.mode in ['clean_urls', 'full_pipeline']:
            run_url_cleaner(args)

        if args.mode in ['formatter', 'full_pipeline']:
            run_formatter(args)

        if args.mode in ['index_updater', 'full_pipeline']:
            run_index_updater(args)

        if args.mode in ['sender', 'full_pipeline']:
            run_sender(args)

        if args.mode in ['subscriber_manager', 'full_pipeline']:
            run_subscriber_manager(args)

        logger.info("Newsletter pipeline completed successfully")

    except Exception as e:
        logger.error(f"Error in newsletter pipeline: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
