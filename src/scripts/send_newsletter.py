import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
import argparse
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Load environment variables from .env file
load_dotenv()

# Get logger
logger = logging.getLogger('send_newsletter')

# Email configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.getenv("NEWSLETTER_EMAIL")
SENDER_PASSWORD = os.getenv("NEWSLETTER_PASSWORD")

# Google Sheets API configuration
SPREADSHEET_ID = os.getenv('GOOGLE_SHEET_ID')
RANGE_NAME = 's1!B:B'  # Column B (netfang) in sheet s1


def get_credentials_dict():
    """Construct credentials dictionary from environment variables."""
    return {
        "type": "service_account",
        "project_id": "newsletter-459520",
        "private_key_id": os.getenv("private_key_id"),
        "private_key": os.getenv("private_key").replace("\\n", "\n"),
        "client_email": "newsletter@newsletter-459520.iam.gserviceaccount.com",
        "client_id": "107370184352758572751",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/newsletter%40newsletter-459520.iam.gserviceaccount.com",
        "universe_domain": "googleapis.com"
    }


def get_active_subscribers():
    """Get list of active subscribers from Google Sheets."""
    try:
        # Create credentials from environment variables
        credentials_dict = get_credentials_dict()
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict,
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


def get_newsletter_by_date(date_str):
    """Get newsletter content for a specific date."""
    newsletters_dir = Path('src/outputs/formatted_newsletters')
    if not newsletters_dir.exists():
        logger.error("Newsletters directory not found")
        return None

    # Try to parse the date
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        logger.error(f"Invalid date format. Please use YYYY-MM-DD")
        return None

    # Get all HTML files
    html_files = []
    for type_dir in newsletters_dir.iterdir():
        if type_dir.is_dir() and 'archived' not in type_dir.name.lower():
            html_files.extend(type_dir.glob('*.html'))

    if not html_files:
        logger.error("No newsletter files found")
        return None

    # Find file matching the date
    for file in html_files:
        try:
            # Get date part from filename (last part before .html)
            # Get the last part after underscore
            file_date_str = file.stem.split('_')[-1]
            file_date = datetime.strptime(file_date_str, '%Y-%m-%d')
            if file_date.date() == target_date.date():
                logger.info(f"Found newsletter file: {file}")
                with open(file, 'r', encoding='utf-8') as f:
                    return f.read()
        except (ValueError, IndexError) as e:
            logger.debug(
                f"Could not parse date from filename {file}: {str(e)}")
            continue

    logger.error(f"No newsletter found for date {date_str}")
    return None


def get_newsletter_by_filename(filename):
    """Get newsletter content for a specific filename."""
    newsletters_dir = Path('src/outputs/formatted_newsletters')
    if not newsletters_dir.exists():
        logger.error("Newsletters directory not found")
        return None

    # Try to find the file
    for type_dir in newsletters_dir.iterdir():
        if type_dir.is_dir() and 'archived' not in type_dir.name.lower():
            file_path = type_dir / filename
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        return f.read()
                except Exception as e:
                    logger.error(f"Error reading newsletter file: {e}")
                    return None

    logger.error(f"No newsletter found with filename {filename}")
    return None


def get_latest_newsletter():
    """Get the latest newsletter content."""
    newsletters_dir = Path('src/outputs/formatted_newsletters')
    if not newsletters_dir.exists():
        logger.error("Newsletters directory not found")
        return None

    # Get all HTML files
    html_files = []
    for type_dir in newsletters_dir.iterdir():
        if type_dir.is_dir() and 'archived' not in type_dir.name.lower():
            html_files.extend(type_dir.glob('*.html'))

    if not html_files:
        logger.error("No newsletter files found")
        return None

    # Sort by date (newest first)
    html_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    latest_file = html_files[0]

    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        logger.error(f"Error reading newsletter file: {e}")
        return None


def create_email_html(newsletter_content):
    """Create the HTML email template."""
    today = datetime.now().strftime("%d. %B %Y")

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                text-align: center;
                padding: 20px;
                background-color: #f8f9fa;
                border-radius: 8px;
                margin-bottom: 20px;
            }}
            .content {{
                background-color: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .footer {{
                text-align: center;
                margin-top: 20px;
                padding: 20px;
                color: #666;
                font-size: 0.9em;
            }}
            a {{
                color: #2563eb;
                text-decoration: none;
            }}
            a:hover {{
                text-decoration: underline;
            }}
        </style>
    </head>
    <body>
        <div class="content">
            {newsletter_content}
        </div>
    </body>
    </html>
    """
    return html


def send_newsletter(newsletter_content=None, date=None, filename=None):
    """Send the newsletter to all active subscribers."""
    if not all([SENDER_EMAIL, SENDER_PASSWORD]):
        logger.error(
            "Email configuration missing. Please set NEWSLETTER_EMAIL and NEWSLETTER_PASSWORD in .env file")
        return

    # Get active subscribers from Google Sheets
    subscribers = get_active_subscribers()
    if not subscribers:
        logger.warning("No active subscribers found")
        return

    # Get newsletter content based on provided parameters
    if newsletter_content is None:
        if date:
            newsletter_content = get_newsletter_by_date(date)
        elif filename:
            newsletter_content = get_newsletter_by_filename(filename)
        else:
            newsletter_content = get_latest_newsletter()

    if not newsletter_content:
        logger.error("No newsletter content found")
        return

    # Create email template
    email_html = create_email_html(newsletter_content)
    subject = f"Daglegt Fréttabréf - sent {datetime.now().strftime('%d-%m-%Y')}"

    # Send to each subscriber
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            subscribers = ['mrbadboy0110@gmail.com']
            for subscriber in subscribers:
                try:
                    # Create a new message for each recipient
                    msg = MIMEMultipart('alternative')
                    msg['Subject'] = subject
                    msg['From'] = SENDER_EMAIL
                    msg['To'] = subscriber
                    msg.attach(MIMEText(email_html, 'html'))

                    server.send_message(msg)
                    logger.info(f"Newsletter sent to {subscriber}")
                except Exception as e:
                    logger.error(f"Error sending to {subscriber}: {e}")
                    continue

    except Exception as e:
        logger.error(f"Error connecting to SMTP server: {e}")
        return

    logger.info(f"Newsletter sent to {len(subscribers)} subscribers")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Send newsletter to subscribers')
    parser.add_argument(
        '--date', help='Date of newsletter to send (YYYY-MM-DD)')
    parser.add_argument('--file', help='Filename of newsletter to send')
    args = parser.parse_args()

    send_newsletter(date=args.date, filename=args.file)
