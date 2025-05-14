#!/usr/bin/env python3
from logger_config import get_logger
import os
from pathlib import Path
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Load environment variables from .env file
load_dotenv()

# Get logger
logger = get_logger('process_unsubscribes')

# Google Sheets API configuration
ACTIVE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
UNSUB_SHEET_ID = os.getenv('GOOGLE_SHEET_ID_UNSUB')
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


def get_sheets_service():
    """Create and return a Google Sheets service."""
    credentials_dict = get_credentials_dict()
    credentials = service_account.Credentials.from_service_account_info(
        credentials_dict,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    service = build("sheets", "v4", credentials=credentials)
    return service.spreadsheets()


def get_unsubscribed_emails():
    """Get list of unsubscribed emails from the unsubscribe sheet."""
    try:
        service = get_sheets_service()
        result = service.values().get(
            spreadsheetId=UNSUB_SHEET_ID,
            range=RANGE_NAME
        ).execute()

        values = result.get('values', [])
        if not values:
            logger.warning('No data found in unsubscribe spreadsheet')
            return []

        # Skip header row and get email addresses
        unsubscribed = [row[0] for row in values[1:] if row]
        return unsubscribed

    except HttpError as e:
        logger.error(f"Error fetching unsubscribed emails: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return []


def get_active_subscribers():
    """Get list of active subscribers with their row numbers."""
    try:
        service = get_sheets_service()
        result = service.values().get(
            spreadsheetId=ACTIVE_SHEET_ID,
            range=RANGE_NAME
        ).execute()

        values = result.get('values', [])
        if not values:
            logger.warning('No data found in active subscribers spreadsheet')
            return []

        # Skip header row and get email addresses with their row numbers
        subscribers = [(i+2, row[0])
                       for i, row in enumerate(values[1:]) if row]
        return subscribers

    except HttpError as e:
        logger.error(f"Error fetching active subscribers: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return []


def remove_unsubscribed_emails(unsubscribed_emails):
    """Clear cells containing unsubscribed emails from the active subscribers sheet."""
    try:
        service = get_sheets_service()
        active_subscribers = get_active_subscribers()

        # Find cells to clear
        cells_to_clear = []
        for row_num, email in active_subscribers:
            if email in unsubscribed_emails:
                # Column B, specific row
                logger.info(f"Clearing cell {row_num} for email {email}")
                cells_to_clear.append(f's1!B{row_num}')

        if not cells_to_clear:
            logger.info("No unsubscribed emails found in active subscribers")
            return

        # Clear each cell
        for cell_range in cells_to_clear:
            try:
                service.values().clear(
                    spreadsheetId=ACTIVE_SHEET_ID,
                    range=cell_range
                ).execute()
                logger.info(f"Cleared cell {cell_range}")
            except HttpError as e:
                logger.error(f"Error clearing cell {cell_range}: {e}")
                continue

    except HttpError as e:
        logger.error(f"Error clearing unsubscribed emails: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


def clear_unsubscribe_sheet():
    """Clear the unsubscribe sheet except for the header row."""
    try:
        service = get_sheets_service()
        # Clear all rows except the header
        range_to_clear = 's1!B2:B'  # Start from B2 to preserve header
        service.values().clear(
            spreadsheetId=UNSUB_SHEET_ID,
            range=range_to_clear
        ).execute()
        logger.info("Cleared unsubscribe sheet")

    except HttpError as e:
        logger.error(f"Error clearing unsubscribe sheet: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


def process_unsubscribes():
    """Process unsubscribes from the unsubscribe sheet."""
    logger.info("Starting unsubscribe processing...")

    # Get unsubscribed emails
    unsubscribed_emails = get_unsubscribed_emails()
    if not unsubscribed_emails:
        logger.info("No unsubscribed emails to process")
        return

    logger.info(f"Found {len(unsubscribed_emails)} unsubscribed emails")

    # Remove unsubscribed emails from active subscribers
    remove_unsubscribed_emails(unsubscribed_emails)

    # Clear the unsubscribe sheet
    clear_unsubscribe_sheet()

    logger.info("Unsubscribe processing completed")


if __name__ == "__main__":
    process_unsubscribes()
