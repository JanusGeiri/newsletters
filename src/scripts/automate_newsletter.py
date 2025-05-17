#!/usr/bin/env python3
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

from nl_formatter.newsletter_formatter import NewsletterFormatter
from nl_formatter.update_index import NewsletterIndexUpdater

from nl_generator.newsletter_generator import NewsletterGenerator
from nl_article_processor.article_group_processor import ArticleGroupProcessor
from nl_article_processor.similarity_strategies import JaccardSimilarity

from nl_scraper.master_scraper import MasterScraper

from nl_sender.process_unsubscribes import SubscriberManager
from nl_sender.send_newsletter import NewsletterSender

from nl_utils.date_utils import get_yesterday_date
from nl_utils.logger_config import setup_logger

# Add src to Python path
sys.path.append(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

# Load environment variables
load_dotenv()

# Set up logging first, before importing other modules
logger = setup_logger(name=__name__, configure_debug=False)


def main():
    """Main automation function."""
    try:
        # Control which processes run

        dev_mode_flag = False

        if dev_mode_flag:
            yesterday = '2025-05-16'
            process_flags = {
                'unsubscribes': False,
                'scraping': False,
                'article_groups': True,  # New flag for article group processing
                'total_generation': False,
                'generation': False,
                'matching': False,
                'impacts': False,
                'formatting': False,
                'index_update': False,
                'sending': False
            }
        else:
            yesterday = get_yesterday_date()
            process_flags = {
                'unsubscribes': True,
                'scraping': True,
                'article_groups': True,
                'total_generation': True,
                'generation': True,
                'matching': True,
                'impacts': False,
                'formatting': True,
                'index_update': True,
                'sending': True
            }

        args = type('Args', (), {
            'date': yesterday,
            'verbose': False,
            'sources': ['visir', 'mbl', 'vb', 'ruv'],
        })

        logger.info("Starting newsletter automation pipeline")
        logger.info("Process flags: %s", process_flags)

        # Step 1: Process unsubscribes
        logger.info("Step 1/6: Processing unsubscribes")
        manager = SubscriberManager()
        manager.process_unsubscribes(ignore=not process_flags['unsubscribes'])
        logger.info("✓ Unsubscribe processing completed")

        # Get yesterday's date
        logger.info("Processing newsletter for date: %s", yesterday)

        # Step 2: Scrape news articles
        logger.info("Step 2/6: Starting news scraping")

        # Initialize master scraper
        master_scraper = MasterScraper(debug_mode=args.verbose)

        # Run the scraper
        logger.info("Running news scraper...")
        output_file = master_scraper.run_scraper(
            date=datetime.strptime(yesterday, '%Y-%m-%d'),
            sources=args.sources,
            ignore=not process_flags['scraping']
        )

        if not output_file:
            logger.error("✗ Failed to scrape articles")
            return
        logger.info("✓ News scraping completed")

        # Step 3: Process article groups
        logger.info("Step 3/6: Processing article groups")
        # Initialize with basic Jaccard similarity strategy
        similarity_strategy = JaccardSimilarity()
        article_processor = ArticleGroupProcessor(
            similarity_strategy=similarity_strategy,
            debug_mode=args.verbose
        )
        article_groups_file = article_processor.run_processor(
            yesterday, ignore=not process_flags['article_groups'])
        if not article_groups_file:
            logger.error("✗ Failed to process article groups")
            return
        logger.info("✓ Article group processing completed")

        # Step 4: Generate newsletter or run matching
        logger.info("Step 4/6: Starting newsletter processing")
        generator = NewsletterGenerator(debug_mode=args.verbose)

        # Run full generation process
        logger.info("Running newsletter generator...")
        output_file = generator.run_generator(
            date_str=yesterday,
            ignore=not process_flags['total_generation'],
            ignore_generation=not process_flags['generation'],
            ignore_impacts=not process_flags['impacts'],
            ignore_matching=not process_flags['matching']
        )

        if not output_file:
            logger.error("✗ Failed to process newsletter")
            return
        logger.info("✓ Newsletter processing completed")

        # Step 5: Format the newsletter
        logger.info("Step 5/6: Formatting newsletter")
        formatter = NewsletterFormatter()
        output_file = formatter.format_newsletter(
            date_str=yesterday,
            file_path=None,  # Let it find the most recent file
            ignore=not process_flags['formatting']
        )
        if not output_file:
            logger.error("✗ Failed to format newsletter")
            return
        logger.info("✓ Newsletter formatting completed")

        # Step 6: Update the index
        logger.info("Step 6/6: Updating newsletter index")
        index_updater = NewsletterIndexUpdater()
        index_updater.update_index(ignore=not process_flags['index_update'])
        logger.info("✓ Index update completed")

        # Step 7: Send the newsletter
        logger.info("Step 7/7: Sending newsletter")
        # Always use dev mode in automation
        sender = NewsletterSender(dev_mode=dev_mode_flag)
        sender.send_newsletter(
            date=yesterday, ignore=not process_flags['sending'])
        logger.info("✓ Newsletter sending completed")

        logger.info("✓ Newsletter automation pipeline completed successfully")

    except Exception as e:
        logger.error("✗ Error in newsletter automation: %s", str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
