#!/usr/bin/env python3
from send_newsletter import send_newsletter
from update_index import update_index
from main import run_scraper, run_generator, run_formatter
from process_unsubscribes import process_unsubscribes
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
from logger_config import setup_logger

# Load environment variables
load_dotenv()

# Set up logging first, before importing other modules
# Will use timestamp-based filename
logger = setup_logger(name='automate_newsletter')
logger.info("Starting newsletter automation process")

# Import functions from other modules after logger setup


def get_yesterday_date():
    """Get yesterday's date in YYYY-MM-DD format."""
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime('%Y-%m-%d')


def main():
    """Main automation function."""
    try:
        # Step 1: Process unsubscribes
        logger.info("Processing unsubscribes...")
        process_unsubscribes()
        logger.info("Unsubscribe processing completed successfully")

        # Get yesterday's date
        yesterday = get_yesterday_date()
        logger.info(f"Processing newsletter for date: {yesterday}")

        # Step 2: Generate the newsletter
        logger.info("Starting newsletter generation...")
        # These arguments will be passed to the functions when implemented
        args = type('Args', (), {
            'mode': 'full_pipeline',
            'date': yesterday,
            'daily_morning': True,
            'verbose': False,
            'sources': ['visir', 'mbl', 'vb', 'ruv'],  # Add all news sources
            'sample_size': 200,  # Default sample size
            'all_types': False,
            'daily_noon': False,
            'daily_evening': False,
            'weekly': False
        })

        # Run the full pipeline
        run_scraper(args)
        run_generator(args)
        run_formatter(args)
        logger.info("Newsletter generation completed successfully")

        # Step 3: Update the index
        logger.info("Updating index...")
        update_index()
        logger.info("Updating index completed successfully")

        # Step 4: Send the newsletter
        logger.info("Sending newsletter...")
        send_newsletter(date=yesterday)
        logger.info("Newsletter sending completed successfully")

        logger.info("Newsletter automation completed successfully")

    except Exception as e:
        logger.error(f"Error in newsletter automation: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
