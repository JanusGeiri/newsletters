#!/usr/bin/env python3
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta
import re
from bs4 import BeautifulSoup
from logger_config import get_logger

# Load environment variables
load_dotenv()

# Get logger
logger = get_logger('update_index')


def get_newsletter_files():
    """Get all newsletter files from the daily_morning directory."""
    newsletter_dir = Path('src/outputs/formatted_newsletters/daily_morning')
    if not newsletter_dir.exists():
        logger.warning(f"Newsletter directory not found: {newsletter_dir}")
        return []

    # Get all HTML files and sort by date (newest first)
    files = list(newsletter_dir.glob('daily_morning_*.html'))
    # Sort by filename date instead of modification time for more reliable ordering
    files.sort(key=lambda x: extract_date_from_filename(x) or '', reverse=True)
    logger.info(f"Found {len(files)} newsletter files")
    return files


def extract_date_from_filename(filename):
    """Extract date from filename in format YYYY-MM-DD."""
    match = re.search(
        r'daily_morning_(\d{4}-\d{2}-\d{2})\.html', filename.name)
    if match:
        return match.group(1)
    return None


def update_index_html():
    """Update index.html with latest newsletter links."""
    # Read the current index.html
    index_path = Path('index.html')
    if not index_path.exists():
        logger.error(f"Index file not found: {index_path}")
        return

    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')

        # Get newsletter files
        newsletter_files = get_newsletter_files()
        if not newsletter_files:
            logger.warning("No newsletter files found!")
            return

        # Update latest newsletter section
        latest_section = soup.find('div', class_='latest-newsletter')
        if latest_section:
            # This will now be the newest file
            latest_file = newsletter_files[0]
            latest_date = extract_date_from_filename(latest_file)
            if latest_date:
                latest_link = latest_section.find('a')
                if latest_link:
                    latest_link[
                        'href'] = f'/newsletters/src/outputs/formatted_newsletters/daily_morning/{latest_file.name}'
                    latest_title = latest_link.find('h3')
                    if latest_title:
                        news_date = datetime.strptime(latest_date, '%Y-%m-%d')
                        send_date = news_date + timedelta(days=1)
                        latest_title.string = f'Fréttabréf ({latest_date}) - sent {send_date.strftime("%Y-%m-%d")}'
                        logger.info(
                            f"Updated latest newsletter link for date: {latest_date}")

        # Update all newsletters section
        newsletter_list = soup.find('div', class_='newsletter-list')
        if newsletter_list:
            # Clear existing links
            newsletter_list.clear()

            # Add new links (already sorted by date in reverse chronological order)
            for file in newsletter_files:
                date = extract_date_from_filename(file)
                if date:
                    news_date = datetime.strptime(date, '%Y-%m-%d')
                    send_date = news_date + timedelta(days=1)
                    link = soup.new_tag('a', href=f'/newsletters/src/outputs/formatted_newsletters/daily_morning/{file.name}',
                                        attrs={'class': 'newsletter-link'})
                    card = soup.new_tag(
                        'div', attrs={'class': 'newsletter-card'})
                    title = soup.new_tag('h3')
                    title.string = f'Fréttabréf ({date}) - sent {send_date.strftime("%Y-%m-%d")}'
                    card.append(title)
                    link.append(card)
                    newsletter_list.append(link)

            logger.info(
                f"Updated newsletter list with {len(newsletter_files)} entries")

        # Write updated index.html
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        logger.info("Successfully wrote updated index.html")

    except Exception as e:
        logger.error(f"Error updating index.html: {str(e)}")
        raise


def update_index():
    """Update the index of newsletters."""
    try:
        logger.info("Starting index update...")
        update_index_html()
        logger.info("Index update completed successfully")

    except Exception as e:
        logger.error(f"Error updating index: {str(e)}")
        raise


if __name__ == "__main__":
    update_index()
