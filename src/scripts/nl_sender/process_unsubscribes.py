#!/usr/bin/env python3
import os
from typing import List, Dict, Any
from dotenv import load_dotenv

from google.oauth2 import service_account
from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError

from nl_utils.logger_config import get_logger, get_module_name
# Load environment variables from .env file
load_dotenv()

# Get logger
logger = get_logger(get_module_name(__name__))

# Google Sheets API configuration
ACTIVE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
UNSUB_SHEET_ID = os.getenv('GOOGLE_SHEET_ID_UNSUB')
RANGE_NAME = 's1!B:B'  # Column B (netfang) in sheet s1


class SubscriberManager:
    """Class to handle subscriber management operations."""

    def __init__(self, debug_mode: bool = False):
        """Initialize the SubscriberManager.

        Args:
            debug_mode (bool): Whether to enable debug mode
        """
        self.logger = logger
        self.debug_mode = debug_mode
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate the Google Sheets configuration."""
        if not all([ACTIVE_SHEET_ID, UNSUB_SHEET_ID]):
            raise ValueError(
                "Google Sheets configuration missing. Please set GOOGLE_SHEET_ID and GOOGLE_SHEET_ID_UNSUB in .env file"
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

    def _get_sheets_service(self) -> Resource:
        """Create and return a Google Sheets service.

        Returns:
            Resource: Google Sheets service resource
        """
        credentials_dict = self._get_credentials_dict()
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        service = build("sheets", "v4", credentials=credentials)
        return service.spreadsheets()

    def get_unsubscribed_emails(self) -> List[str]:
        """Get list of unsubscribed emails from the unsubscribe sheet.

        Returns:
            List[str]: List of unsubscribed email addresses
        """
        try:
            service = self._get_sheets_service()
            result = service.values().get(
                spreadsheetId=UNSUB_SHEET_ID,
                range=RANGE_NAME
            ).execute()

            values = result.get('values', [])
            if not values:
                self.logger.warning('No data found in unsubscribe spreadsheet')
                return []

            # Skip header row and get email addresses
            unsubscribed = [row[0] for row in values[1:] if row]
            return unsubscribed

        except HttpError as e:
            self.logger.error("Error fetching unsubscribed emails: %s", str(e))
            return []
        except Exception as e:
            self.logger.error("Unexpected error: %s", str(e))
            return []

    def get_active_subscribers(self) -> List[tuple[int, str]]:
        """Get list of active subscribers with their row numbers.

        Returns:
            List[tuple[int, str]]: List of tuples containing row numbers and email addresses
        """
        try:
            service = self._get_sheets_service()
            result = service.values().get(
                spreadsheetId=ACTIVE_SHEET_ID,
                range=RANGE_NAME
            ).execute()

            values = result.get('values', [])
            if not values:
                self.logger.warning(
                    'No data found in active subscribers spreadsheet')
                return []

            # Skip header row and get email addresses with their row numbers
            subscribers = [(i+2, row[0])
                           for i, row in enumerate(values[1:]) if row]
            return subscribers

        except HttpError as e:
            self.logger.error("Error fetching active subscribers: %s", str(e))
            return []
        except Exception as e:
            self.logger.error("Unexpected error: %s", str(e))
            return []

    def remove_unsubscribed_emails(self, unsubscribed_emails: List[str]) -> None:
        """Clear cells containing unsubscribed emails from the active subscribers sheet.

        Args:
            unsubscribed_emails (List[str]): List of email addresses to remove
        """
        try:
            service = self._get_sheets_service()
            active_subscribers = self.get_active_subscribers()

            # Find cells to clear
            cells_to_clear = []
            for row_num, email in active_subscribers:
                if email in unsubscribed_emails:
                    # Column B, specific row
                    self.logger.info(
                        "Clearing cell %d for email %s", row_num, email)
                    cells_to_clear.append(f's1!B{row_num}')

            if not cells_to_clear:
                self.logger.info(
                    "No unsubscribed emails found in active subscribers")
                return

            # Clear each cell
            for cell_range in cells_to_clear:
                try:
                    service.values().clear(
                        spreadsheetId=ACTIVE_SHEET_ID,
                        range=cell_range
                    ).execute()
                    self.logger.info("Cleared cell %s", cell_range)
                except HttpError as e:
                    self.logger.error(
                        "Error clearing cell %s: %s", cell_range, str(e))
                    continue

        except HttpError as e:
            self.logger.error("Error clearing unsubscribed emails: %s", str(e))
        except Exception as e:
            self.logger.error("Unexpected error: %s", str(e))

    def clear_unsubscribe_sheet(self) -> None:
        """Clear the unsubscribe sheet except for the header row."""
        try:
            service = self._get_sheets_service()
            # Clear all rows except the header
            range_to_clear = 's1!B2:B'  # Start from B2 to preserve header
            service.values().clear(
                spreadsheetId=UNSUB_SHEET_ID,
                range=range_to_clear
            ).execute()
            self.logger.info("Cleared unsubscribe sheet")

        except HttpError as e:
            self.logger.error("Error clearing unsubscribe sheet: %s", str(e))
        except Exception as e:
            self.logger.error("Unexpected error: %s", str(e))

    def process_unsubscribes(self, ignore: bool = False) -> None:
        """Process unsubscribes from the unsubscribe sheet.

        Args:
            ignore (bool): If True, skip processing and return immediately
        """
        if ignore:
            self.logger.info("Ignoring unsubscribe processing operation")
            return

        try:
            self.logger.info("Starting unsubscribe processing...")

            # Get unsubscribed emails
            unsubscribed_emails = self.get_unsubscribed_emails()
            if not unsubscribed_emails:
                self.logger.info("No unsubscribed emails to process")
                return

            self.logger.info("Found %d unsubscribed emails",
                             len(unsubscribed_emails))

            # Remove unsubscribed emails from active subscribers
            self.remove_unsubscribed_emails(unsubscribed_emails)

            # Clear the unsubscribe sheet
            self.clear_unsubscribe_sheet()

            self.logger.info("Unsubscribe processing completed")

        except Exception as e:
            self.logger.error("Error in unsubscribe processing: %s", str(e))
            raise


def process_unsubscribes(ignore: bool = False) -> None:
    """Legacy function to maintain backward compatibility.

    Args:
        ignore (bool): If True, skip processing and return immediately
    """
    nl_subscriber_manager = SubscriberManager()
    nl_subscriber_manager.process_unsubscribes(ignore=ignore)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description='Process newsletter unsubscribes')
    parser.add_argument('--ignore', action='store_true',
                        help='Ignore unsubscribe processing')
    args = parser.parse_args()

    subscriber_manager = SubscriberManager()
    subscriber_manager.process_unsubscribes(ignore=args.ignore)
