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
from logger_config import get_logger

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
    try:
        logger.info("Starting news scraper")

        # Get today's date
        today = datetime.now().date()
        if args.date:
            today = datetime.strptime(args.date, '%Y-%m-%d').date()

        # Initialize scrapers
        visir_scraper = VisirScraper(debug_mode=args.verbose)
        mbl_scraper = MblScraper(debug_mode=args.verbose)
        vb_scraper = VbScraper(debug_mode=args.verbose)
        ruv_scraper = RUVScraper(debug_mode=args.verbose)

        # Process articles from all sources
        all_articles = []

        if 'visir' in args.sources:
            visir_articles = visir_scraper.process_articles(today)
            all_articles.extend(visir_articles)
            logger.info(f"Processed {len(visir_articles)} Visir articles")

        if 'mbl' in args.sources:
            mbl_articles = mbl_scraper.process_articles(today)
            all_articles.extend(mbl_articles)
            logger.info(f"Processed {len(mbl_articles)} MBL articles")

        if 'vb' in args.sources:
            vb_articles = vb_scraper.process_articles(today)
            all_articles.extend(vb_articles)
            logger.info(f"Processed {len(vb_articles)} VB articles")

        if 'ruv' in args.sources:
            ruv_articles = ruv_scraper.process_articles(today)
            all_articles.extend(ruv_articles)
            logger.info(f"Processed {len(ruv_articles)} RUV articles")

        # Save to JSON file
        output_file = Path("src/outputs/news/json") / \
            f"news_articles_{today}.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_articles, f, ensure_ascii=False, indent=2)

        logger.info(
            f"Saved {len(all_articles)} total articles to {output_file}")

    except Exception as e:
        logger.error(f"Error in news scraper: {str(e)}")
        raise


def run_generator(args) -> None:
    """Run the newsletter generator.

    Args:
        args: Command line arguments.
    """
    try:
        logger.info("Starting newsletter generator")

        # Get newsletter types to generate
        newsletter_types = get_newsletter_types(args)
        if not newsletter_types:
            logger.error("No newsletter types specified")
            return

        # Process each newsletter type
        for newsletter_type in newsletter_types:
            try:
                logger.info(
                    f"Generating {newsletter_type.value} newsletter...")

                # Load news data
                articles, date_str = load_news_data(
                    args.date,
                    args.sample_size,
                    newsletter_type
                )

                if not articles:
                    logger.error(
                        f"No articles found for {newsletter_type.value} newsletter")
                    continue

                # Generate newsletter
                newsletter_content = generate_newsletter(
                    articles, newsletter_type, date_str)

                if not newsletter_content:
                    logger.error(
                        f"Failed to generate {newsletter_type.value} newsletter")
                    continue

                # Save newsletter
                output_file = save_newsletter(
                    newsletter_content, date_str, newsletter_type)

                if output_file:
                    logger.info(
                        f"Saved {newsletter_type.value} newsletter to: {output_file}")
                else:
                    logger.error(
                        f"Failed to save {newsletter_type.value} newsletter")

            except Exception as e:
                logger.error(
                    f"Error generating {newsletter_type.value} newsletter: {str(e)}")
                continue

    except Exception as e:
        logger.error(f"Error in newsletter generator: {str(e)}")
        raise


def run_formatter(args) -> None:
    """Run the newsletter formatter.

    Args:
        args: Command line arguments.
    """
    try:
        logger.info("Starting newsletter formatter")

        # Get newsletter types to process
        newsletter_types = get_newsletter_types(args)
        if not newsletter_types:
            logger.error("No newsletter types specified")
            return

        for newsletter_type in newsletter_types:
            try:
                logger.info(
                    f"Formatting {newsletter_type.value} newsletter...")

                # Read the newsletter content
                content, date_str, input_file = read_newsletter_file(
                    date_str=args.date,
                    file_path=None,  # Let it find the most recent file
                    increment=1,
                    newsletter_type=newsletter_type
                )

                if not content:
                    logger.error(
                        f"No content found for {newsletter_type.value} newsletter")
                    continue

                # Format the content as HTML
                html_content = format_newsletter_html(content)

                if not html_content:
                    logger.error(
                        f"Failed to format {newsletter_type.value} newsletter")
                    continue

                # Save the formatted newsletter
                output_file = save_formatted_newsletter(
                    html_content, date_str, newsletter_type)

                if output_file:
                    logger.info(
                        f"Formatted newsletter saved to: {output_file}")
                else:
                    logger.error(
                        f"Failed to save formatted {newsletter_type.value} newsletter")

            except Exception as e:
                logger.error(
                    f"Error formatting {newsletter_type.value} newsletter: {str(e)}")
                continue

    except Exception as e:
        logger.error(f"Error in newsletter formatter: {str(e)}")
        raise


def main():
    """Main function to run the newsletter pipeline."""
    try:
        logger.info("Starting newsletter pipeline")

        # Parse command line arguments
        parser = argparse.ArgumentParser(
            description='Run the newsletter pipeline')
        parser.add_argument('--mode', choices=['scraper', 'generator', 'formatter', 'full_pipeline'],
                            default='full_pipeline', help='Pipeline mode to run')
        parser.add_argument('--date', help='Date to process (YYYY-MM-DD)')
        parser.add_argument('--daily_morning', action='store_true',
                            help='Generate daily morning newsletter')
        parser.add_argument('--verbose', action='store_true',
                            help='Enable verbose output')
        parser.add_argument('--sources', nargs='+', default=['visir', 'mbl', 'vb', 'ruv'],
                            help='News sources to process')
        parser.add_argument('--sample_size', type=int, default=200,
                            help='Number of articles to sample')
        parser.add_argument('--all_types', action='store_true',
                            help='Generate all newsletter types')
        parser.add_argument('--daily_noon', action='store_true',
                            help='Generate daily noon newsletter')
        parser.add_argument('--daily_evening', action='store_true',
                            help='Generate daily evening newsletter')
        parser.add_argument('--weekly', action='store_true',
                            help='Generate weekly newsletter')

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

        if args.mode in ['formatter', 'full_pipeline']:
            run_formatter(args)

        logger.info("Newsletter pipeline completed successfully")

    except Exception as e:
        logger.error(f"Error in newsletter pipeline: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
