#!/usr/bin/env python3
import os
import sys
import json
import argparse
from datetime import datetime
from dotenv import load_dotenv

from nl_formatter.newsletter_formatter import NewsletterFormatter
from nl_formatter.update_index import NewsletterIndexUpdater

from nl_generator.newsletter_generator import NewsletterGenerator
from nl_article_processor.article_group_processor import ArticleGroupProcessor
from nl_article_processor.clustering_strategies import AgglomerativeClusteringStrategy
from nl_article_processor.similarity_strategies import (
    JaccardSimilarity,
    LSASimilarity,
    EnhancedJaccardSimilarity,
    LDASimilarity,
    BERTSimilarity
)

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

# LSA similarity configuration
lsa_similarity_params = {'n_components': 80}
lsa_similarity_strategy = LSASimilarity(params=lsa_similarity_params)

# Jaccard similarity configuration
jaccard_similarity_params = {}
jaccard_similarity_strategy = JaccardSimilarity(
    params=jaccard_similarity_params)

# Enhanced Jaccard similarity configuration
enhanced_jaccard_similarity_params = {}
enhanced_jaccard_similarity_strategy = EnhancedJaccardSimilarity(
    params=enhanced_jaccard_similarity_params)

# LDA similarity configuration
lda_similarity_params = {
    'n_topics': 20,
    'max_iter': 100
}
lda_similarity_strategy = LDASimilarity(params=lda_similarity_params)

# BERT similarity configuration
bert_similarity_params = {
    'model_name': 'all-MiniLM-L6-v2',
    'device': 'cpu'
}
bert_similarity_strategy = BERTSimilarity(params=bert_similarity_params)

similarity_strategies = {
    'lsa': {
        'strategy': lsa_similarity_strategy,
        'params': lsa_similarity_params
    },
    'jaccard': {
        'strategy': jaccard_similarity_strategy,
        'params': jaccard_similarity_params
    },
    'enhanced_jaccard': {
        'strategy': enhanced_jaccard_similarity_strategy,
        'params': enhanced_jaccard_similarity_params
    },
    'lda': {
        'strategy': lda_similarity_strategy,
        'params': lda_similarity_params
    },
    'bert': {
        'strategy': bert_similarity_strategy,
        'params': bert_similarity_params
    }
}


def main():
    """Main automation function."""
    try:
        # Set up argument parser
        parser = argparse.ArgumentParser(description='Newsletter automation script')
        parser.add_argument('--test', action='store_true', help='Run in test mode with all process flags set to false')
        parser.add_argument('--date', type=str, help='Date to process (YYYY-MM-DD format)')
        parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
        parser.add_argument('--sources', nargs='+', default=['visir', 'mbl', 'vb', 'ruv'],
                            help='News sources to scrape')
        args = parser.parse_args()

        # Control which processes run
        dev_mode_flag = True

        if args.test:
            yesterday = args.date if args.date else datetime.now().strftime('%Y-%m-%d')
            process_flags = {
                'unsubscribes': False,
                'scraping': False,
                'article_groups': False,
                'total_generation': False,
                'generation': False,
                'matching': False,
                'impacts': False,
                'formatting': False,
                'index_update': False,
                'sending': False
            }
        elif dev_mode_flag:
            yesterday = '2025-05-19'
            process_flags = {
                'unsubscribes': False,
                'scraping': False,
                'article_groups': False,
                'total_generation': False,
                'generation': False,
                'matching': False,
                'impacts': False,
                'formatting': False,
                'index_update': True,
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

        # Convert args to the expected format
        args = type('Args', (), {
            'date': yesterday,
            'verbose': args.verbose,
            'sources': args.sources,
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

        sim_strat_choice = 'lsa'
        similarity_strategy = similarity_strategies[sim_strat_choice]['strategy']
        similarity_params = similarity_strategies[sim_strat_choice]['params']

        clustering_strategy = AgglomerativeClusteringStrategy(
            params={
                'n_clusters': None,
                'distance_threshold': 0.67,
                'similarity_strategy': similarity_strategy,
                'similarity_params': similarity_params
            }
        )
        article_processor = ArticleGroupProcessor(
            params={
                'clustering_strategy': clustering_strategy,
                'similarity_strategy': similarity_strategy
            },
            debug_mode=args.verbose
        )
        article_groups_file = article_processor.run_processor(
            yesterday, ignore=not process_flags['article_groups'])
        if not article_groups_file:
            logger.error("✗ Failed to process article groups")
            return
        logger.info("✓ Article group processing completed")

        # Log article groups in dev mode
        if dev_mode_flag and process_flags['article_groups']:
            logger.info("Article Groups Summary:")
            with open(article_groups_file, 'r', encoding='utf-8') as f:
                article_groups = json.load(f)
                for group in article_groups['groups']:
                    logger.info("Group: %s", group['details']['group_name'])
                    logger.info("Articles:")
                    for article in group['details']['articles']:
                        logger.info("- %s", article['title'])

        # Save similarity logs
        if dev_mode_flag:
            logger.info("Saving similarity logs...")
            similarity_strategy.save_similarity_log()
            logger.info("✓ Similarity logs saved")

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
