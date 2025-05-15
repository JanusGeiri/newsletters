"""
RSS feed handler for fetching and processing RSS feeds from various news sources.
"""
from datetime import datetime
import feedparser
from nl_utils.logger_config import get_logger

# Get logger
logger = get_logger('rss_handler')


class RSSFeedHandler:
    """Handles fetching and processing of RSS feeds from various news sources"""

    def __init__(self):
        self.feed_links = {
            'visir': [
                'https://www.visir.is/rss/frettir',
                'https://www.visir.is/rss/vidskipti',
                'https://www.visir.is/rss/sport',
                'https://www.visir.is/rss/lifid',
                'https://www.visir.is/rss/skodun',
                'https://www.visir.is/rss/innherji'
            ],
            'mbl': [
                "https://www.mbl.is/feeds/fp/",
                "https://www.mbl.is/feeds/innlent/",
                "https://www.mbl.is/feeds/erlent/",
                "https://www.mbl.is/feeds/togt/",
                "https://www.mbl.is/feeds/vidskipti/",
                "https://www.mbl.is/feeds/200milur/",
                "https://www.mbl.is/feeds/sport/",
                "https://www.mbl.is/feeds/fotbolti/",
                "https://www.mbl.is/feeds/enski/",
                "https://www.mbl.is/feeds/golf/",
                "https://www.mbl.is/feeds/handbolti/",
                "https://www.mbl.is/feeds/korfubolti/",
                "https://www.mbl.is/feeds/pepsideild/",
                "https://www.mbl.is/feeds/formula/",
                "https://www.mbl.is/feeds/rafithrottir/",
                "https://www.mbl.is/feeds/folk/",
                "https://www.mbl.is/feeds/verold/",
                "https://www.mbl.is/feeds/matur/",
                "https://www.mbl.is/feeds/ferdalog/",
                "https://www.mbl.is/feeds/smartland/",
                "https://www.mbl.is/feeds/stars/",
                "https://www.mbl.is/feeds/tiska/",
                "https://www.mbl.is/feeds/heimili/",
                "https://www.mbl.is/feeds/utlit/",
                "https://www.mbl.is/feeds/heilsa/",
                "https://www.mbl.is/feeds/frami/",
                "https://www.mbl.is/feeds/samkvaemislifid/",
                "https://www.mbl.is/feeds/fjolskyldan/",
                "https://www.mbl.is/feeds/k100/",
                "https://www.mbl.is/feeds/blog/"
            ],
            'vb': [
                'https://www.vb.is/rss'
            ],
            'ruv': [
                'https://www.ruv.is/rss/frettir',
                'https://www.ruv.is/rss/innlent',
                'https://www.ruv.is/rss/erlent',
                'https://www.ruv.is/rss/ithrottir',
                'https://www.ruv.is/rss/menning-og-daegurmal'
            ]
        }

    def get_articles(self, source=None):
        """Get articles from RSS feeds

        Args:
            source: Optional source name to filter feeds by (e.g., 'visir', 'mbl')

        Returns:
            List of article dictionaries
        """
        articles = []
        processed_urls = set()  # Keep track of processed URLs to avoid duplicates

        # If source is specified, only process feeds for that source
        sources_to_process = [source] if source else self.feed_links.keys()

        for source_name in sources_to_process:
            if source_name not in self.feed_links:
                logger.warning("Unknown source: %s", source_name)
                continue

            for feed_url in self.feed_links[source_name]:
                try:
                    feed = feedparser.parse(feed_url)
                    for entry in feed.entries:
                        # Skip if we've already processed this URL
                        if entry.link in processed_urls:
                            continue

                        # Use feedparser's parsed date if available, otherwise use published
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            date_obj = datetime(*entry.published_parsed[:6])
                            formatted_date = date_obj.strftime(
                                "%Y-%m-%d %H:%M:%S")
                        else:
                            formatted_date = None

                        article = {
                            "article_source": source_name,
                            "article_title": entry.title,
                            "article_date": formatted_date,
                            "article_description": entry.description,
                            "article_url": entry.link,
                        }
                        articles.append(article)
                        # Add URL to processed set
                        processed_urls.add(entry.link)
                except Exception as e:
                    logger.error("Error fetching feed %s: %s",
                                 feed_url, str(e))
        return articles
