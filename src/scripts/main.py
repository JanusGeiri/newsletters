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
from logger_config import get_logger, setup_logger

# Import modules
from newsletter_generator import (
    generate_newsletter, save_newsletter,
    load_news_data, insert_impacts, clean_urls_in_newsletter
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


def run_impacts(args) -> None:
    """Run the impact insertion process.

    Args:
        args: Command line arguments.
    """
    try:
        logger.info("Starting impact insertion")

        # Get the newsletter file
        newsletters_dir = Path('src/outputs/newsletters/daily_morning')
        if args.date:
            newsletter_file = newsletters_dir / \
                f'daily_morning_{args.date}.json'
        else:
            # Find the most recent file
            files = list(newsletters_dir.glob("*.json"))
            if not files:
                logger.error("No newsletter files found")
                return
            newsletter_file = max(files, key=lambda x: x.stat().st_mtime)

        if not newsletter_file.exists():
            logger.error(f"No newsletter file found: {newsletter_file}")
            return

        # Insert impacts
        try:
            success = insert_impacts(newsletter_file)
            if success:
                logger.info(
                    f"Successfully inserted impacts into: {newsletter_file}")
            else:
                logger.error(
                    f"Failed to insert impacts into: {newsletter_file}")
        except Exception as e:
            logger.error(f"Error inserting impacts: {str(e)}")

    except Exception as e:
        logger.error(f"Error in impact insertion: {str(e)}")
        raise


def run_generator(args) -> None:
    """Run the newsletter generator.

    Args:
        args: Command line arguments.
    """
    try:
        logger.info("Starting newsletter generator")

        # Process each newsletter type
        try:
            logger.info(f"Generating newsletter...")

            # Load news data
            articles, date_str = load_news_data(
                args.date,
                args.sample_size
            )

            if not articles:
                logger.error(f"No articles found for newsletter")

            # Generate newsletter
            newsletter_content = generate_newsletter(
                articles, date_str)

            if not newsletter_content:
                logger.error(f"Failed to generate newsletter")

            # Save newsletter
            output_file = save_newsletter(
                newsletter_content, date_str)

            if output_file:
                logger.info(
                    f"Saved newsletter initial content to: {output_file}")
            else:
                logger.error(f"Failed to save initial newsletter content")

        except Exception as e:
            logger.error(f"Error generating newsletter: {str(e)}")

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

        try:
            logger.info(f"Formatting newsletter...")

            # Read the newsletter content
            content, date_str, input_file = read_newsletter_file(
                date_str=args.date,
                file_path=None,  # Let it find the most recent file
            )

            if not content:
                logger.error(f"No content found for newsletter")
                return

            # Format the content as HTML
            html_content = format_newsletter_html(content)

            if not html_content:
                logger.error(f"Failed to format newsletter")
                return

            # Save the formatted newsletter
            output_file = save_formatted_newsletter(
                html_content, date_str)

            if output_file:
                logger.info(f"Formatted newsletter saved to: {output_file}")
            else:
                logger.error(f"Failed to save formatted newsletter")

        except Exception as e:
            logger.error(f"Error formatting newsletter: {str(e)}")
            raise

    except Exception as e:
        logger.error(f"Error in newsletter formatter: {str(e)}")
        raise


def run_url_cleaner(args) -> None:
    """Run the URL cleaning process.

    Args:
        args: Command line arguments.
    """
    try:
        logger.info("Starting URL cleaning process")

        # Get the newsletter file
        newsletters_dir = Path('src/outputs/newsletters/daily_morning')
        if args.date:
            newsletter_file = newsletters_dir / \
                f'daily_morning_{args.date}.json'
        else:
            # Find the most recent file
            files = list(newsletters_dir.glob("*.json"))
            if not files:
                logger.error("No newsletter files found")
                return
            newsletter_file = max(files, key=lambda x: x.stat().st_mtime)

        if not newsletter_file.exists():
            logger.error(f"No newsletter file found: {newsletter_file}")
            return

        # Load the newsletter
        with open(newsletter_file, 'r', encoding='utf-8') as f:
            newsletter_json = json.load(f)

        # Clean URLs
        try:
            cleaned_newsletter = clean_urls_in_newsletter(newsletter_json)

            # Save the cleaned newsletter
            with open(newsletter_file, 'w', encoding='utf-8') as f:
                json.dump(cleaned_newsletter, f, ensure_ascii=False, indent=2)

            logger.info(f"Successfully cleaned URLs in: {newsletter_file}")

        except Exception as e:
            logger.error(f"Error cleaning URLs: {str(e)}")

    except Exception as e:
        logger.error(f"Error in URL cleaning process: {str(e)}")
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
        parser.add_argument('--mode', choices=['scraper', 'generator', 'formatter', 'impacts', 'clean_urls', 'full_pipeline'],
                            default='full_pipeline', help='Pipeline mode to run')
        parser.add_argument('--date', help='Date to process (YYYY-MM-DD)')
        parser.add_argument('--verbose', action='store_true',
                            help='Enable verbose output')
        parser.add_argument('--sources', nargs='+', default=['visir', 'mbl', 'vb', 'ruv'],
                            help='News sources to process')
        parser.add_argument('--sample_size', type=int, default=200,
                            help='Number of articles to sample')
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

        logger.info("Newsletter pipeline completed successfully")

    except Exception as e:
        logger.error(f"Error in newsletter pipeline: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
