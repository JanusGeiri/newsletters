from flask import Flask, render_template, send_file, request, redirect, url_for, flash
from pathlib import Path
from datetime import datetime
import logging
from translations import TRANSLATIONS
import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required for flash messages

# Google Sheets API configuration
SPREADSHEET_ID = os.getenv('GOOGLE_SHEET_ID')
RANGE_NAME = 's1!B:B'  # Column B (netfang) in sheet s1


def get_subscribers():
    """Get list of subscribers from Google Sheets."""
    try:
        credentials = service_account.Credentials.from_service_account_file(
            "creds.json",
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
        )
        service = build("sheets", "v4", credentials=credentials)
        sheet = service.spreadsheets()
        result = sheet.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME
        ).execute()

        values = result.get('values', [])
        if not values:
            logger.warning('No data found in spreadsheet')
            return []

        # Skip header row and get email addresses
        subscribers = [row[0] for row in values[1:]
                       if row]  # Get first (and only) column
        return subscribers

    except HttpError as e:
        logger.error(f"Error fetching subscribers from Google Sheets: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return []


def get_newsletter_files():
    """Get all newsletter HTML files."""
    newsletters_dir = Path('outputs/formatted_newsletters')
    newsletters = []

    logger.info(f"Scanning directory: {newsletters_dir}")

    if not newsletters_dir.exists():
        logger.error(
            f"Newsletters directory does not exist: {newsletters_dir}")
        return newsletters

    # Walk through all newsletter type directories
    for type_dir in newsletters_dir.iterdir():
        if not type_dir.is_dir():
            continue

        # Skip archived directories
        if 'archived' in type_dir.name.lower():
            logger.info(f"Skipping archived directory: {type_dir}")
            continue

        logger.info(f"Processing directory: {type_dir}")

        # Get all HTML files in this directory
        html_files = list(type_dir.glob('*.html'))
        logger.info(f"Found {len(html_files)} HTML files in {type_dir}")

        for file in html_files:
            # Skip archived files
            if 'archived' in file.name.lower():
                logger.info(f"Skipping archived file: {file}")
                continue

            # Extract date from filename (assuming format includes date at end)
            filename_parts = file.stem.split('_')
            date_str = filename_parts[-1] if len(filename_parts) > 1 else ''

            # Try to parse the date, use current time if invalid
            try:
                timestamp = datetime.strptime(date_str, '%Y-%m-%d').timestamp()
            except ValueError:
                timestamp = datetime.now().timestamp()
                date_str = datetime.now().strftime('%Y-%m-%d')

            newsletter_data = {
                'type': type_dir.name,
                'date': date_str,
                'title': file.stem.replace('_', ' ').title(),
                'path': str(file.relative_to('outputs/formatted_newsletters')),
                'timestamp': timestamp
            }
            newsletters.append(newsletter_data)
            logger.info(f"Added newsletter: {newsletter_data}")

    # Sort by date, newest first
    newsletters.sort(key=lambda x: x['timestamp'], reverse=True)
    logger.info(f"Total newsletters found: {len(newsletters)}")
    return newsletters


@app.route('/')
def home():
    """Render the home page with newsletter links."""
    newsletters = get_newsletter_files()
    latest = newsletters[0] if newsletters else None

    # Get unique newsletter types
    newsletter_types = sorted(list(set(n['type'] for n in newsletters)))

    # Get selected type from query parameter
    selected_type = request.args.get('type', '')

    # Filter newsletters by type if selected
    if selected_type:
        newsletters = [n for n in newsletters if n['type'] == selected_type]
        latest = newsletters[0] if newsletters else None

    return render_template('index.html',
                           latest=latest,
                           newsletters=newsletters,
                           newsletter_types=newsletter_types,
                           selected_type=selected_type,
                           t=TRANSLATIONS['is'])


@app.route('/newsletter/<path:filename>')
def serve_newsletter(filename):
    """Serve a newsletter HTML file."""
    return send_file(f'outputs/formatted_newsletters/{filename}')


if __name__ == '__main__':
    app.run(debug=True)
