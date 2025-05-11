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

# Import modules
from newsletter_schemas import NewsletterType
from newsletter_generator import (
    generate_newsletter, save_newsletter,
    load_news_data
)
from news_scraper import (
    VisirScraper, MblScraper, VbScraper, RUVScraper
)
from newsletter_formatter import (
    read_newsletter_file, format_newsletter_html,
    save_formatted_newsletter
)
from openai import OpenAI

# Set up logging directory
LOGS_DIR = Path('logs')
LOGS_DIR.mkdir(exist_ok=True)

# Generate timestamp for log file
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
log_file = LOGS_DIR / f'newsletter_{timestamp}.log'

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)
logger.info(f"Starting new run. Log file: {log_file}")


class RunMode(Enum):
    """Different modes of operation for the newsletter system."""
    SCRAPE_ONLY = "scrape_only"
    GENERATE_ONLY = "generate_only"
    FORMAT_ONLY = "format_only"
    FULL_PIPELINE = "full_pipeline"
    # New mode for generation and formatting without scraping
    GENERATE_AND_FORMAT = "generate_and_format"


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


def get_newsletter_types(args) -> List[NewsletterType]:
    """Get list of newsletter types to generate based on arguments.

    Args:
        args: Command line arguments.

    Returns:
        List[NewsletterType]: List of newsletter types to generate.
    """
    types = []
    if args.all_types:
        return list(NewsletterType)

    if args.daily_morning:
        types.append(NewsletterType.DAILY_MORNING)
    if args.daily_noon:
        types.append(NewsletterType.DAILY_NOON)
    if args.daily_evening:
        types.append(NewsletterType.DAILY_EVENING)
    if args.weekly:
        types.append(NewsletterType.WEEKLY)

    return types


def run_scraper(args) -> None:
    """Run the news scraper.

    Args:
        args: Command line arguments.
    """
    logger.info("Starting news scraping...")

    # Initialize scrapers
    scrapers = {
        'visir': VisirScraper(debug_mode=args.verbose),
        'mbl': MblScraper(debug_mode=args.verbose),
        'vb': VbScraper(debug_mode=args.verbose),
        'ruv': RUVScraper(debug_mode=args.verbose)
    }

    # Filter scrapers based on sources argument
    if args.sources:
        scrapers = {k: v for k, v in scrapers.items() if k in args.sources}

    # Convert date string to datetime object
    target_date = datetime.strptime(args.date, '%Y-%m-%d').date()

    # Process articles from each source
    all_articles = []
    for source_name, scraper in scrapers.items():
        try:
            logger.info(f"Processing articles from {source_name}...")
            articles = scraper.process_articles(target_date)
            all_articles.extend(articles)
            logger.info(
                f"Processed {len(articles)} articles from {source_name}")
        except Exception as e:
            logger.error(f"Error processing {source_name}: {str(e)}")

    # Save combined articles
    if all_articles:
        output_file = Path("outputs/news/json") / \
            f"news_articles_{args.date}.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_articles, f, ensure_ascii=False, indent=2)
        logger.info(
            f"Saved {len(all_articles)} total articles to {output_file}")
    else:
        logger.warning("No articles were processed")


def run_generator(args) -> None:
    """Run the newsletter generator.

    Args:
        args: Command line arguments.
    """
    logger.info("Starting newsletter generation...")
    newsletter_types = get_newsletter_types(args)

    for newsletter_type in newsletter_types:
        try:
            logger.info(f"Generating {newsletter_type.value} newsletter...")

            # Load articles for the newsletter type
            articles, date_str = load_news_data(
                date_str=args.date,
                sample_size=args.sample_size,
                newsletter_type=newsletter_type
            )

            if not articles:
                logger.warning(
                    f"No articles found for {newsletter_type.value} newsletter")
                continue

            # Generate newsletter content
            newsletter_content = generate_newsletter(
                articles=articles,
                newsletter_type=newsletter_type,
                date_str=date_str
            )

            # Save the newsletter
            output_file = save_newsletter(
                newsletter_content=newsletter_content,
                date_str=date_str,
                newsletter_type=newsletter_type
            )

            logger.info(
                f"{newsletter_type.value} newsletter saved to: {output_file}")

        except Exception as e:
            logger.error(
                f"Error generating {newsletter_type.value} newsletter: {str(e)}")


def run_formatter(args) -> None:
    """Run the newsletter formatter.

    Args:
        args: Command line arguments.
    """
    logger.info("Starting newsletter formatting...")
    newsletter_types = get_newsletter_types(args)

    for newsletter_type in newsletter_types:
        try:
            logger.info(f"Formatting {newsletter_type.value} newsletter...")

            # Read the newsletter content
            content, date_str, input_file = read_newsletter_file(
                date_str=args.date,
                file_path=None,  # Let it find the most recent file
                increment=1,
                newsletter_type=newsletter_type
            )

            # Format the content as HTML
            html_content = format_newsletter_html(content)

            # Save the formatted newsletter
            output_file = save_formatted_newsletter(
                html_content=html_content,
                date_str=date_str,
                newsletter_type=newsletter_type
            )
            logger.info(f"Formatted newsletter saved to: {output_file}")

        except Exception as e:
            logger.error(
                f"Error formatting {newsletter_type.value} newsletter: {str(e)}")


def main():
    parser = argparse.ArgumentParser(
        description='Newsletter generation pipeline')

    # Mode selection
    parser.add_argument('--mode', type=str, choices=[m.value for m in RunMode],
                        default=RunMode.FULL_PIPELINE.value,
                        help='Operation mode')

    # Date handling
    parser.add_argument('--date', type=str,
                        help='Date for newsletter (YYYY-MM-DD). Defaults to today')

    # Newsletter type selection
    type_group = parser.add_mutually_exclusive_group()
    type_group.add_argument('--all-types', action='store_true',
                            help='Generate all types of newsletters')
    type_group.add_argument('--daily-morning', action='store_true',
                            help='Generate daily morning newsletter')
    type_group.add_argument('--daily-noon', action='store_true',
                            help='Generate daily noon newsletter')
    type_group.add_argument('--daily-evening', action='store_true',
                            help='Generate daily evening newsletter')
    type_group.add_argument('--weekly', action='store_true',
                            help='Generate weekly newsletter')

    # Scraper settings
    scraper_group = parser.add_argument_group('Scraper Settings')
    scraper_group.add_argument('--sources', type=str, nargs='+',
                               choices=['visir', 'mbl', 'vb', 'ruv'],
                               help='News sources to scrape')
    scraper_group.add_argument('--max-articles', type=int, default=200,
                               help='Maximum number of articles to scrape')

    # Generator settings
    generator_group = parser.add_argument_group('Generator Settings')
    generator_group.add_argument('--sample-size', type=int, default=200,
                                 help='Number of articles to sample for generation')
    generator_group.add_argument('--temperature', type=float, default=0.8,
                                 help='Temperature for text generation')
    generator_group.add_argument('--max-tokens', type=int, default=6500,
                                 help='Maximum tokens for generation')

    # General settings
    parser.add_argument('--verbose', action='store_true',
                        help='Enable verbose logging')
    parser.add_argument('--dry-run', action='store_true',
                        help='Run without making changes')

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Validate date
    try:
        args.date = parse_date(args.date)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)

    # Run selected mode
    try:
        if args.mode in [RunMode.SCRAPE_ONLY.value, RunMode.FULL_PIPELINE.value]:
            run_scraper(args)

        if args.mode in [RunMode.GENERATE_ONLY.value, RunMode.FULL_PIPELINE.value, RunMode.GENERATE_AND_FORMAT.value]:
            run_generator(args)

        if args.mode in [RunMode.FORMAT_ONLY.value, RunMode.FULL_PIPELINE.value, RunMode.GENERATE_AND_FORMAT.value]:
            run_formatter(args)

    except Exception as e:
        logger.error(f"Error in {args.mode}: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
