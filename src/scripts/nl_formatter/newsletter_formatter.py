#!/usr/bin/env python3
from datetime import datetime
import argparse
import sys
import logging
from typing import Tuple, Optional, Dict, Any

from nl_utils.logger_config import get_logger, get_module_name
from nl_utils.file_handler import FileHandler, FileType
from .html_templates import NewsletterTemplate

# Get logger
logger = get_logger(get_module_name(__name__))


class NewsletterFormatter:
    """Class for formatting newsletter content."""

    def __init__(self):
        """Initialize the newsletter formatter."""
        self.logger = get_logger(get_module_name(__name__))
        self.template = NewsletterTemplate()
        self.file_handler = FileHandler()

    def get_date_from_filename(self, filename: str) -> Tuple[Optional[str], Optional[int]]:
        """Extract date and increment from newsletter filename."""
        return self.file_handler.extract_date_from_filename(filename)

    def read_newsletter_file(self, date_str: Optional[str] = None, file_path: Optional[str] = None) -> Tuple[Dict[str, Any], str, str]:
        """Read a newsletter file and return its content.

        Args:
            date_str (Optional[str]): Date string in YYYY-MM-DD format
            file_path (Optional[str]): Path to the newsletter file

        Returns:
            Tuple[Dict[str, Any], str, str]: Content, date string, and input file path
        """
        try:
            self.logger.debug("Reading newsletter file for date: %s", date_str)

            if file_path:
                # If file path is provided, load from that specific file
                content = self.file_handler.load_file(
                    FileType.PROCESSED_NEWSLETTER,
                    base_name=file_path
                )
                date_str, _ = self.get_date_from_filename(file_path)
            else:
                # Otherwise, load the most recent file for the given date
                content = self.file_handler.load_file(
                    FileType.PROCESSED_NEWSLETTER,
                    date_str=date_str,
                    base_name="newsletter_processed"
                )

            if not content:
                raise FileNotFoundError(
                    f"No newsletter found for date: {date_str}")

            return content, date_str, file_path or f"newsletter_processed_{date_str}.json"

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

            # Add main headline and summary section with impact
            html_sections.append(self.template.create_summary_html(
                main_headline=content.get('main_headline', ''),
                summary=content.get('summary', ''),
                summary_impact=content.get('summary_impact'),
                summary_impact_urls=content.get('summary_impact_urls')
            ))

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

            # Process all sections except closing_summary
            for section_key, section_header in self.template.TEXT_CONFIG['sections'].items():
                if section_key == 'closing_summary' or section_key not in content or not content[section_key]:
                    continue

                section_items = []
                for item in content[section_key]:
                    if not isinstance(item, dict):
                        self.logger.warning(
                            "Skipping invalid item in %s: %s", section_key, item)
                        continue

                    # Create news item HTML with the new structure
                    section_items.append(self.template.create_news_item_html(
                        title=item.get('title', ''),
                        description=item.get('description', ''),
                        urls=item.get('article_urls', []),
                        tags=item.get('tags', []),
                        impact=item.get('impact'),
                        impact_urls=item.get('impact_urls', []),
                        match=item.get('match')
                    ))

                if section_items:
                    html_sections.append(self.template.create_section_html(
                        section_key,
                        section_header,
                        ''.join(section_items)
                    ))

            # Add closing summary section if it exists
            if 'closing_summary' in content and content['closing_summary']:
                html_sections.append(self.template.create_section_html(
                    'closing_summary',
                    self.template.TEXT_CONFIG['sections']['closing_summary'],
                    f'<p>{self.template.format_text(content["closing_summary"])}</p>'
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

    def save_formatted_newsletter(self, html_content: str, date_str: str) -> str:
        """Save the formatted newsletter to a file.

        Args:
            html_content (str): The HTML content to save
            date_str (str): Date string in YYYY-MM-DD format

        Returns:
            str: Path to the saved file
        """
        try:
            file_path = self.file_handler.save_file(
                content=html_content,
                file_type=FileType.FORMATTED_NEWSLETTER,
                date_str=date_str,
                base_name="newsletter_formatted"
            )
            return str(file_path)
        except Exception as e:
            self.logger.error("Error saving formatted newsletter: %s", str(e))
            raise

    def format_newsletter(
        self,
        date_str: Optional[str] = None,
        file_path: Optional[str] = None,
        ignore: bool = False
    ) -> str:
        """Format a newsletter and save it to a file.

        Args:
            date_str (Optional[str]): Date string in YYYY-MM-DD format
            file_path (Optional[str]): Path to the newsletter file
            ignore (bool): If True, skip formatting and return a dummy path

        Returns:
            str: Path to the formatted newsletter file
        """
        if ignore:
            self.logger.info("Ignoring newsletter formatting operation")
            return "src/outputs/newsletters/formatted/dummy.html"

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
            file_path=args.file,
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
