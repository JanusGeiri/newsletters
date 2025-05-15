#!/usr/bin/env python3
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

from main import run_generator, run_impacts, run_url_cleaner
from nl_utils.date_utils import get_yesterday_date
from nl_sender.process_unsubscribes import SubscriberManager
from nl_formatter.update_index import NewsletterIndexUpdater
from nl_sender.send_newsletter import NewsletterSender
from nl_formatter.newsletter_formatter import NewsletterFormatter
from nl_scraper.master_scraper import MasterScraper
from nl_generator.newsletter_generator import NewsletterGenerator
from nl_utils.logger_config import setup_logger

# Add src to Python path
sys.path.append(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

# Load environment variables
load_dotenv()

# Set up logging first, before importing other modules
logger = setup_logger(name='automate_newsletter')


def main():
    """Main automation function."""
    try:
        # Control which processes run
        process_flags = {
            'unsubscribes': True,
            'scraping': True,
            'generation': True,
            'url_cleaning': True,
            'impacts': False,
            'formatting': True,
            'index_update': True,
            'sending': True
        }
        dev_mode_flag = False

        logger.info("Starting newsletter automation process")
        # Step 1: Process unsubscribes
        logger.info("Processing unsubscribes...")
        manager = SubscriberManager()
        manager.process_unsubscribes(ignore=not process_flags['unsubscribes'])
        logger.info("Unsubscribe processing completed successfully")

        # Get yesterday's date
        yesterday = get_yesterday_date()
        yesterday = '2025-05-15'
        logger.info("Processing newsletter for date: %s", yesterday)

        # Step 2: Generate the newsletter
        logger.info("Starting newsletter generation...")
        # These arguments will be passed to the functions when implemented
        args = type('Args', (), {
            'mode': 'full_pipeline',
            'date': yesterday,
            'verbose': False,
            'sources': ['visir', 'mbl', 'vb', 'ruv'],  # Add all news sources
            'sample_size': 200,  # Default sample size
            'input_file': None,
            'ignore': True
        })

        # Initialize master scraper
        master_scraper = MasterScraper(debug_mode=args.verbose)

        # Run the scraper
        output_file = master_scraper.run_scraper(
            date=datetime.strptime(yesterday, '%Y-%m-%d'),
            sources=args.sources,
            ignore=not process_flags['scraping']
        )

        if not output_file:
            logger.error("Failed to scrape articles")
            return

        # Initialize newsletter generator
        generator = NewsletterGenerator(debug_mode=args.verbose)
        articles, date_str = generator.load_news_data(
            yesterday, args.sample_size)
        if not articles or not date_str:
            logger.error("Failed to load news data")
            return

        # Run generator
        output_file = generator.run_generator(
            date_str, articles, ignore=not process_flags['generation'])
        if not output_file:
            logger.error("Failed to generate newsletter")
            return

        # Run URL cleaner
        success = generator.run_url_cleaner(
            date_str, ignore=not process_flags['url_cleaning'])
        if not success:
            logger.error("Failed to clean URLs")
            return

        # # Run impacts
        # success = generator.run_impacts(
        #     date_str, ignore=not process_flags['impacts'])
        # if not success:
        #     logger.error("Failed to insert impacts")
        #     return

        # # Run URL cleaner again
        # success = generator.run_url_cleaner(
        #     date_str, ignore=not process_flags['url_cleaning'])
        # if not success:
        #     logger.error("Failed to clean URLs")
        #     return

        # Format the newsletter
        formatter = NewsletterFormatter()
        output_file = formatter.format_newsletter(
            date_str=yesterday,
            file_path=None,  # Let it find the most recent file
            ignore=not process_flags['formatting']
        )
        logger.info("Newsletter formatting completed successfully")

        # Step 3: Update the index
        logger.info("Updating index...")
        index_updater = NewsletterIndexUpdater()
        index_updater.update_index(ignore=not process_flags['index_update'])
        logger.info("Updating index completed successfully")

        # Step 4: Send the newsletter
        logger.info("Sending newsletter...")
        # Always use dev mode in automation
        sender = NewsletterSender(dev_mode=dev_mode_flag)
        sender.send_newsletter(
            date=yesterday, ignore=not process_flags['sending'])
        logger.info("Newsletter sending completed successfully")

        logger.info("Newsletter automation completed successfully")

    except Exception as e:
        logger.error("Error in newsletter automation: %s", str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
