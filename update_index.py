#!/usr/bin/env python3
import os
from pathlib import Path
from datetime import datetime
import re
from bs4 import BeautifulSoup


def get_newsletter_files():
    """Get all newsletter files from the daily_morning directory."""
    newsletter_dir = Path('outputs/formatted_newsletters/daily_morning')
    if not newsletter_dir.exists():
        return []

    # Get all HTML files and sort by date (newest first)
    files = list(newsletter_dir.glob('daily_morning_*.html'))
    # Sort by filename date instead of modification time for more reliable ordering
    files.sort(key=lambda x: extract_date_from_filename(x) or '', reverse=True)
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
    with open('index.html', 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    # Get newsletter files
    newsletter_files = get_newsletter_files()
    if not newsletter_files:
        print("No newsletter files found!")
        return

    # Update latest newsletter section
    latest_section = soup.find('div', class_='latest-newsletter')
    if latest_section:
        latest_file = newsletter_files[0]  # This will now be the newest file
        latest_date = extract_date_from_filename(latest_file)
        if latest_date:
            latest_link = latest_section.find('a')
            if latest_link:
                latest_link[
                    'href'] = f'/newsletters/outputs/formatted_newsletters/daily_morning/{latest_file.name}'
                latest_title = latest_link.find('h3')
                if latest_title:
                    latest_title.string = f'Fréttabréf ({latest_date})'

    # Update all newsletters section
    newsletter_list = soup.find('div', class_='newsletter-list')
    if newsletter_list:
        # Clear existing links
        newsletter_list.clear()

        # Add new links (already sorted by date in reverse chronological order)
        for file in newsletter_files:
            date = extract_date_from_filename(file)
            if date:
                link = soup.new_tag('a', href=f'/newsletters/outputs/formatted_newsletters/daily_morning/{file.name}',
                                    attrs={'class': 'newsletter-link'})
                card = soup.new_tag('div', attrs={'class': 'newsletter-card'})
                title = soup.new_tag('h3')
                title.string = f'Fréttabréf ({date})'
                card.append(title)
                link.append(card)
                newsletter_list.append(link)

    # Write updated index.html
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(str(soup))


if __name__ == '__main__':
    update_index_html()
