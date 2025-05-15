#!/usr/bin/env python3
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, cast

from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError

from nl_utils.logger_config import get_logger
from nl_utils.load_file import load_formatted_newsletter

# Load environment variables
load_dotenv()

# Get logger
logger = get_logger('send_newsletter')

# Email configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.getenv("NEWSLETTER_EMAIL")
SENDER_PASSWORD = os.getenv("NEWSLETTER_PASSWORD")

# Google Sheets API configuration
SPREADSHEET_ID = os.getenv('GOOGLE_SHEET_ID')
RANGE_NAME = 's1!B:B'  # Column B (netfang) in sheet s1

# Development mode configuration
DEV_EMAIL = 'mrbadboy0110@gmail.com'


class NewsletterSender:
    """Class to handle newsletter sending functionality."""

    def __init__(self, dev_mode: bool = False):
        """Initialize the NewsletterSender.

        Args:
            dev_mode (bool): Whether to run in development mode
        """
        self.dev_mode = dev_mode
        self.logger = logger
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate the email configuration."""
        if not all([SENDER_EMAIL, SENDER_PASSWORD]):
            raise ValueError(
                "Email configuration missing. Please set NEWSLETTER_EMAIL and NEWSLETTER_PASSWORD in .env file"
            )

    def _get_credentials_dict(self) -> Dict[str, Any]:
        """Get Google Sheets API credentials dictionary.

        Returns:
            Dict[str, Any]: Credentials dictionary
        """
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

    def get_active_subscribers(self) -> List[str]:
        """Get list of active subscribers.

        Returns:
            List[str]: List of subscriber email addresses
        """

        try:
            # Create credentials from environment variables
            credentials_dict = self._get_credentials_dict()
            credentials = service_account.Credentials.from_service_account_info(
                credentials_dict,
                scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
            )
            service = build("sheets", "v4", credentials=credentials)
            sheet = cast(Resource, service.spreadsheets())
            result = sheet.values().get(
                spreadsheetId=SPREADSHEET_ID,
                range=RANGE_NAME
            ).execute()

            values = result.get('values', [])
            if not values:
                self.logger.warning('No data found in spreadsheet')
                return []

            # Skip header row and get email addresses
            subscribers = [row[0] for row in values[1:] if row]
            if self.dev_mode:
                self.logger.info("Running in dev mode, using test email")
                self.logger.info("Dev mode: Subscribers: %s", subscribers)
                return [DEV_EMAIL]
            else:
                return subscribers

        except HttpError as e:
            self.logger.error(
                "Error fetching subscribers from Google Sheets: %s", str(e))
            return []
        except Exception as e:
            self.logger.error("Unexpected error: %s", str(e))
            return []

    def _get_newsletter_content(
        self,
        date_str: Optional[str] = None,
        filename: Optional[str] = None
    ) -> Optional[str]:
        """Get newsletter content using utility functions.

        Args:
            date_str (Optional[str]): Date string in YYYY-MM-DD format
            filename (Optional[str]): Name of the newsletter file

        Returns:
            Optional[str]: Newsletter content if found, None otherwise
        """
        try:
            if filename:
                # If filename is provided, use it directly
                file_path = Path(
                    'src/outputs/formatted_newsletters/daily_morning') / filename
                if not file_path.exists():
                    self.logger.error(
                        "Newsletter file not found: %s", file_path)
                    return None
                return file_path.read_text(encoding='utf-8')
            else:
                # Use the utility function to load the newsletter
                content, _, _ = load_formatted_newsletter(
                    date_str=date_str,
                    newsletter_type='daily_morning'
                )
                return content

        except Exception as e:
            self.logger.error("Error getting newsletter content: %s", str(e))
            return None

    def _create_email_html(self, newsletter_content: str) -> str:
        """Create the HTML email template.

        Args:
            newsletter_content (str): Newsletter content to include in the email

        Returns:
            str: HTML email template
        """

        return f"""
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

    def send_newsletter(
        self,
        newsletter_content: Optional[str] = None,
        date: Optional[str] = None,
        filename: Optional[str] = None,
        ignore: bool = False
    ) -> None:
        """Send the newsletter to all active subscribers.

        Args:
            newsletter_content (Optional[str]): Newsletter content to send
            date (Optional[str]): Date of newsletter to send (YYYY-MM-DD)
            filename (Optional[str]): Filename of newsletter to send
            ignore (bool): If True, skip sending and return immediately
        """
        if ignore:
            self.logger.info("Ignoring newsletter send operation")
            return

        # Get active subscribers
        subscribers = self.get_active_subscribers()
        if not subscribers:
            self.logger.warning("No active subscribers found")
            return

        # Get newsletter content based on provided parameters
        if newsletter_content is None:
            newsletter_content = self._get_newsletter_content(date, filename)

        if not newsletter_content:
            self.logger.error("No newsletter content found")
            return

        # Create email template
        email_html = self._create_email_html(newsletter_content)
        subject = f"Daglegt Fréttabréf - sent {datetime.now().strftime('%d-%m-%Y')}"

        # Send to each subscriber
        try:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                for subscriber in subscribers:
                    try:
                        # Create a new message for each recipient
                        msg = MIMEMultipart('alternative')
                        msg['Subject'] = subject
                        msg['From'] = SENDER_EMAIL
                        msg['To'] = subscriber
                        msg.attach(MIMEText(email_html, 'html'))

                        server.send_message(msg)
                        self.logger.info("Newsletter sent to %s", subscriber)
                    except Exception as e:
                        self.logger.error(
                            "Error sending to %s: %s", subscriber, str(e))
                        continue

        except Exception as e:
            self.logger.error("Error connecting to SMTP server: %s", str(e))
            return

        self.logger.info("Newsletter sent to %d subscribers", len(subscribers))


def send_newsletter(date: Optional[str] = None, filename: Optional[str] = None) -> None:
    """Legacy function to maintain backward compatibility.

    Args:
        date (Optional[str]): Date of newsletter to send (YYYY-MM-DD)
        filename (Optional[str]): Filename of newsletter to send
    """
    sender_object = NewsletterSender(dev_mode=False)
    sender_object.send_newsletter(date=date, filename=filename)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description='Send newsletter to subscribers')
    parser.add_argument(
        '--date', help='Date of newsletter to send (YYYY-MM-DD)')
    parser.add_argument('--file', help='Filename of newsletter to send')
    parser.add_argument('--dev', action='store_true',
                        help='Run in development mode')
    args = parser.parse_args()

    sender = NewsletterSender(dev_mode=args.dev)
    sender.send_newsletter(date=args.date, filename=args.file)
