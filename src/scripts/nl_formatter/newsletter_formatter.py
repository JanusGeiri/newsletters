#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import argparse
import sys
import logging
from typing import Tuple, Optional, Dict, Any
from nl_utils.logger_config import get_logger
from nl_utils import load_newsletter_file, save_formatted_newsletter, extract_date_from_filename
from .html_templates import NewsletterTemplate

# Get logger
logger = get_logger('newsletter_formatter')


class NewsletterFormatter:
    """Class for formatting newsletter content."""

    def __init__(self):
        """Initialize the newsletter formatter."""
        self.logger = get_logger('newsletter_formatter')
        self.template = NewsletterTemplate()

    def get_date_from_filename(self, filename: str) -> Tuple[Optional[str], Optional[int]]:
        """Extract date and increment from newsletter filename."""
        return extract_date_from_filename(filename)

    def read_newsletter_file(self, date_str: Optional[str] = None, file_path: Optional[str] = None) -> Tuple[Dict[str, Any], str, Path]:
        """Read a newsletter file and return its content."""
        try:
            self.logger.debug("Reading newsletter file for date: %s", date_str)
            return load_newsletter_file(date_str=date_str, file_path=file_path)
        except Exception as e:
            self.logger.error("Error reading newsletter file: %s", str(e))
            raise

    def format_newsletter_html(self, content: Dict[str, Any]) -> str:
        """Convert JSON newsletter content to HTML format."""
        try:
            self.logger.debug("Formatting newsletter as HTML")

            # Validate required fields
            required_fields = ['main_headline', 'summary']
            missing_fields = [
                field for field in required_fields if field not in content]
            if missing_fields:
                self.logger.error(
                    "Missing required fields in newsletter content: %s", ', '.join(missing_fields))
                raise ValueError(
                    f"Missing required fields: {', '.join(missing_fields)}")

            # Get date from content or use current date
            date_str = content.get('date', datetime.now().strftime('%Y-%m-%d'))

            # Start building HTML sections
            html_sections = []

            # Add title section
            html_sections.append(f"""
            <div class="section title-section">
                <h1 class="newsletter-title">{self.template.TEXT_CONFIG['title']}</h1>
                <h2 class="newsletter-date">{date_str}</h2>
            </div>
            """)

            # Add main headline and summary section
            summary_urls = self.template.create_footnote_links(
                content.get('summary_urls', []), 'summary')
            summary_impact_urls = self.template.create_footnote_links(
                content.get('summary_impact_urls', []), 'impact')

            html_sections.append(f"""
            <div class="section" id="summary">
                <h2 class="main-headline">{content.get('main_headline', '')}</h2>
                <div class="section-content">
                    <p>{self.template.format_text(content.get('summary', ''))} {summary_urls}</p>
                    <p class="impact"><strong>Áhrif:</strong> {self.template.format_text(content.get('summary_impact', ''))} {summary_impact_urls}</p>
                </div>
            </div>
            """)

            # Create table of contents
            toc_items = []
            for section_key, section_title in self.template.TEXT_CONFIG['sections'].items():
                if section_key in content and content[section_key]:
                    toc_items.append(
                        f'<a href="#{section_key}" class="toc-item">{section_title}</a>')

            # Add table of contents section
            if toc_items:
                html_sections.append(self.template.create_toc_html(
                    {k: v for k, v in self.template.TEXT_CONFIG['sections'].items() if k in content and content[k]}))

            # Add key events section
            if 'key_events' in content and content['key_events']:
                key_events_html = []
                for event in content['key_events']:
                    if not isinstance(event, dict):
                        self.logger.warning(
                            "Skipping invalid key event: %s", event)
                        continue

                    key_events_html.append(self.template.create_news_item_html(
                        title=event.get('title', ''),
                        description=event.get('description', ''),
                        urls=event.get('urls', []),
                        tags=event.get('tags', []),
                        impact=event.get('impact', ''),
                        impact_urls=event.get('impact_urls', [])
                    ))

                if key_events_html:
                    html_sections.append(self.template.create_section_html(
                        'key_events',
                        self.template.TEXT_CONFIG['sections']['key_events'],
                        ''.join(key_events_html)
                    ))

            # Add other sections
            for section_key, section_header in self.template.TEXT_CONFIG['sections'].items():
                if section_key in ['key_events', 'closing_summary']:
                    continue

                if section_key in content and content[section_key]:
                    section_items = []
                    for item in content[section_key]:
                        if not isinstance(item, dict):
                            self.logger.warning(
                                "Skipping invalid item in %s: %s", section_key, item)
                            continue

                        section_items.append(self.template.create_news_item_html(
                            title=item.get('title', ''),
                            description=item.get('description', ''),
                            urls=item.get('urls', []),
                            tags=item.get('tags', [])
                        ))

                    if section_items:
                        html_sections.append(self.template.create_section_html(
                            section_key,
                            section_header,
                            ''.join(section_items)
                        ))

            # Add closing summary section
            if 'closing_summary' in content and content['closing_summary']:
                html_sections.append(self.template.create_section_html(
                    'closing_summary',
                    self.template.TEXT_CONFIG['sections']['closing_summary'],
                    f"<p>{self.template.format_text(content['closing_summary'])}</p>"
                ))

            # Add signature section
            html_sections.append(f"""
            <div class="section signature-section">
                <p class="signature">{self.template.TEXT_CONFIG['signature']}</p>
                <p class="unsubscribe"><a href="{self.template.TEXT_CONFIG['unsubscribe_link']}">{self.template.TEXT_CONFIG['unsubscribe_text']}</a></p>
            </div>
            """)

            # Combine sections
            html_content = '\n'.join(html_sections)

            # Create the full HTML email template
            html_template = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    {self.template.get_css_styles()}
                </style>
            </head>
            <body>
                <div class="newsletter-container">
                    {html_content}
                </div>
            </body>
            </html>
            """

            self.logger.info("Newsletter HTML formatting completed")
            return html_template

        except Exception as e:
            self.logger.error("Error formatting newsletter: %s", str(e))
            raise

    def save_formatted_newsletter(self, html_content: str, date_str: str) -> Path:
        """Save the formatted newsletter to a file."""
        try:
            return save_formatted_newsletter(html_content, date_str)
        except Exception as e:
            self.logger.error("Error saving formatted newsletter: %s", str(e))
            raise

    def format_newsletter(
        self,
        date_str: Optional[str] = None,
        file_path: Optional[str] = None,
        ignore: bool = False
    ) -> Path:
        """Format a newsletter and save it to a file.

        Args:
            date_str (Optional[str]): Date string in YYYY-MM-DD format
            file_path (Optional[str]): Path to the newsletter file
            ignore (bool): If True, skip formatting and return a dummy path

        Returns:
            Path: Path to the formatted newsletter file
        """
        if ignore:
            self.logger.info("Ignoring newsletter formatting operation")
            return Path('src/outputs/formatted_newsletters/daily_morning/dummy.html')

        try:
            self.logger.info("Starting newsletter formatting...")

            # Read the newsletter content
            content, date_str, input_file = self.read_newsletter_file(
                date_str=date_str,
                file_path=file_path
            )

            # Log the content structure for debugging
            self.logger.info("Processing newsletter from %s", input_file)
            self.logger.info("Content keys: %s", list(content.keys()))

            # Format the content as HTML
            html_content = self.format_newsletter_html(content)

            # Save the formatted newsletter
            output_file = self.save_formatted_newsletter(
                html_content, date_str)
            self.logger.info("Formatted newsletter saved to: %s", output_file)

            return output_file

        except FileNotFoundError as e:
            self.logger.error("File not found for newsletter: %s", str(e))
            raise
        except ValueError as e:
            self.logger.error("Error formatting newsletter: %s", str(e))
            raise
        except Exception as e:
            self.logger.error(
                "Unexpected error formatting newsletter: %s", str(e))
            self.logger.exception("Detailed error information:")
            raise


def run_formatter(args) -> None:
    """Run the newsletter formatter.

    Args:
        args: Command line arguments.
    """
    logger.info("Starting newsletter formatting...")

    try:
        logger.info("Formatting newsletter...")

        # Initialize the formatter
        formatter = NewsletterFormatter()

        # Format the newsletter
        output_file = formatter.format_newsletter(
            date_str=args.date,
            file_path=None,  # Let it find the most recent file
            ignore=args.ignore
        )

        if output_file:
            logger.info("Formatted newsletter saved to: %s", output_file)
        else:
            logger.error("Failed to save formatted newsletter")

    except Exception as e:
        logger.error("Error formatting newsletter: %s", str(e))
        raise


def main():
    """Main function to run the newsletter formatter."""
    parser = argparse.ArgumentParser(
        description='Format newsletter content into HTML')
    parser.add_argument('--date', help='Date of the newsletter (YYYY-MM-DD)')
    parser.add_argument('--file', help='Path to the newsletter file')
    parser.add_argument('--ignore', action='store_true',
                        help='Ignore newsletter formatting')
    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        run_formatter(args)
    except Exception as e:
        logger.error("Error running formatter: %s", str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
