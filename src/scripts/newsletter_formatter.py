#!/usr/bin/env python3
import os
from pathlib import Path
from datetime import datetime, timedelta
import re
import argparse
import sys
import json
import logging
from typing import Tuple, Optional, List
from logger_config import get_logger

# Get logger
logger = get_logger('newsletter_formatter')


def get_date_from_filename(filename):
    """Extract date and increment from newsletter filename."""
    match = re.search(r'newsletter_(\d{4}-\d{2}-\d{2})(?:_(\d+))?', filename)
    if match:
        date_str = match.group(1)
        increment = int(match.group(2)) if match.group(2) else 1
        return date_str, increment
    return None, None


def read_newsletter_file(date_str: Optional[str] = None, file_path: Optional[str] = None, increment: int = 1) -> Tuple[dict, str, Path]:
    """Read a newsletter file and return its content.

    Args:
        date_str (Optional[str]): Date string in YYYY-MM-DD format. If None, use current date.
        file_path (Optional[str]): Path to the newsletter file. If None, find the most recent file.
        increment (int): Increment number for the newsletter file.

    Returns:
        Tuple[dict, str, Path]: Tuple containing the newsletter content as a dict, date string, and input file path.
    """
    try:
        logger.debug(f"Reading newsletter file for date: {date_str}")

        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')

        # Create base newsletters directory
        newsletters_dir = Path('src/outputs/newsletters/daily_morning')

        # Initialize input_file
        input_file = None

        if file_path:
            input_file = Path(file_path)
        else:
            # First try to find a file matching the exact date
            base_filename = f'{date_str}'
            if increment > 1:
                base_filename = f'{base_filename}_{increment}'

            input_file = newsletters_dir / f'{base_filename}.json'

            # If no file exists for the specified date, find the most recent file
            if not input_file.exists():
                files = list(newsletters_dir.glob(f'{date_str}_*.json'))
                if not files:
                    # If no files found for the date, look for any files
                    files = list(newsletters_dir.glob('*.json'))
                    if not files:
                        raise FileNotFoundError(f"No newsletter files found")

                # Sort files by modification time (newest first)
                files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

                # If date is specified, try to find the most recent file before or on that date
                if date_str:
                    target_date = datetime.strptime(date_str, '%Y-%m-%d')
                    for file in files:
                        # Get date part from filename
                        file_date_str = file.stem.split('_')[0]
                        try:
                            file_date = datetime.strptime(
                                file_date_str, '%Y-%m-%d')
                            if file_date <= target_date:
                                input_file = file
                                break
                        except ValueError:
                            continue
                    else:
                        # If no file found before or on the specified date, use the most recent file
                        input_file = files[0]
                else:
                    # If no date specified, use the most recent file
                    input_file = files[0]

        if not input_file.exists():
            raise FileNotFoundError(f"Newsletter file not found: {input_file}")

        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                content = json.load(f)

            # Validate content is a dictionary
            if not isinstance(content, dict):
                raise ValueError(
                    f"Invalid JSON content in {input_file}: expected dictionary, got {type(content)}")

            # Log the keys we found for debugging
            logger.info(
                f"Found keys in newsletter content: {list(content.keys())}")

            return content, date_str, input_file

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from {input_file}: {str(e)}")
            raise ValueError(f"Invalid JSON content in {input_file}") from e
    except Exception as e:
        logger.error(
            f"Error reading newsletter file {input_file if 'input_file' in locals() else 'unknown'}: {str(e)}")
        raise


def format_newsletter_html(content):
    """Convert JSON newsletter content to HTML format."""
    try:
        logger.debug("Formatting newsletter as HTML")

        # Parse JSON content
        if isinstance(content, str):
            try:
                content = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON content: {str(e)}")
                raise ValueError("Invalid JSON content") from e

        # Validate required fields
        required_fields = ['main_headline', 'summary']
        missing_fields = [
            field for field in required_fields if field not in content]
        if missing_fields:
            logger.error(
                f"Missing required fields in newsletter content: {', '.join(missing_fields)}")
            raise ValueError(
                f"Missing required fields: {', '.join(missing_fields)}")

        # Helper function to convert text with line breaks to HTML
        def format_text(text):
            if not text:
                return ""
            return text.replace('\n\n', '<br><br>').replace('\n', '<br>')

        # Helper function to create footnote links
        def create_footnote_links(urls, prefix=''):
            if not urls:
                return ""
            links = []
            for i, url in enumerate(urls, 1):
                footnote_id = f"{prefix}fn{i}"
                links.append(
                    f'<a href="{url}" class="footnote-link" data-tooltip="{url}" id="{footnote_id}">[{i}]</a>')
            return ' '.join(links)

        # Get date from content or use current date
        date_str = content.get('date', datetime.now().strftime('%Y-%m-%d'))
        title = 'Fréttir Gærdagsins'

        # Start building HTML sections
        html_sections = []

        # Add title section
        html_sections.append(f"""
        <div class="section title-section">
            <h1 class="newsletter-title">{title}</h1>
            <h2 class="newsletter-date">{date_str}</h2>
        </div>
        """)

        # Add main headline and summary section
        summary_urls = create_footnote_links(
            content.get('summary_urls', []), 'summary')
        summary_impact_urls = create_footnote_links(
            content.get('summary_impact_urls', []), 'impact')

        html_sections.append(f"""
        <div class="section" id="summary">
            <h2 class="main-headline">{content.get('main_headline', '')}</h2>
            <div class="section-content">
                <p>{format_text(content.get('summary', ''))} {summary_urls}</p>
                <p class="impact"><strong>Áhrif:</strong> {format_text(content.get('summary_impact', ''))} {summary_impact_urls}</p>
            </div>
        </div>
        """)

        # Create table of contents
        toc_items = []
        section_mapping = {
            'key_events': '1. MIKILVÆGUSTU FRÉTTIRNAR',
            'domestic_news': '2. INNLENT',
            'foreign_news': '3. ERLENT',
            'business': '4. VIÐSKIPTI',
            'famous_people': '5. FRÆGA FÓLKIÐ',
            'sports': '6. ÍÞRÓTTIR',
            'arts': '7. LISTIR',
            'science': '8. VÍSINDI',
            'closing_summary': '9. LOKAORÐ'
        }

        # Add sections to TOC if they have content
        for section_key, section_title in section_mapping.items():
            if section_key in content and content[section_key]:
                toc_items.append(
                    f'<a href="#{section_key}" class="toc-item">{section_title}</a>')

        # Add table of contents section
        if toc_items:
            html_sections.append(f"""
            <div class="section toc-section">
                <h2 class="section-header">Efnisyfirlit</h2>
                <div class="toc-container">
                    {''.join(toc_items)}
                </div>
            </div>
            """)

        # Add key events section
        if 'key_events' in content and content['key_events']:
            key_events_html = []
            for event in content['key_events']:
                if not isinstance(event, dict):
                    logger.warning(f"Skipping invalid key event: {event}")
                    continue

                event_urls = create_footnote_links(
                    event.get('urls', []), 'event')
                impact_urls = create_footnote_links(
                    event.get('impact_urls', []), 'impact')

                key_events_html.append(f"""
                <div class="news-item">
                    <h3>{event.get('title', '')}</h3>
                    <p>{format_text(event.get('description', ''))} {event_urls}</p>
                    <p class="impact"><strong>Áhrif:</strong> {format_text(event.get('impact', ''))} {impact_urls}</p>
                    <div class="tags">
                        {', '.join(
                            f'<span class="tag">{tag}</span>' for tag in event.get('tags', []))}
                    </div>
                </div>
                """)

            if key_events_html:
                html_sections.append(f"""
                <div class="section" id="key_events">
                    <h2 class="section-header">1. MIKILVÆGUSTU FRÉTTIRNAR:</h2>
                    <div class="section-content">
                        {''.join(key_events_html)}
                    </div>
                </div>
                """)

        # Add other sections
        section_mapping = {
            'domestic_news': '2. INNLENT:',
            'foreign_news': '3. ERLENT:',
            'business': '4. VIÐSKIPTI:',
            'famous_people': '5. FRÆGA FÓLKIÐ:',
            'sports': '6. ÍÞRÓTTIR:',
            'arts': '7. LISTIR:',
            'science': '8. VÍSINDI:'
        }

        for section_key, section_header in section_mapping.items():
            if section_key in content and content[section_key]:
                section_items = []
                for item in content[section_key]:
                    if not isinstance(item, dict):
                        logger.warning(
                            f"Skipping invalid item in {section_key}: {item}")
                        continue

                    item_urls = create_footnote_links(
                        item.get('urls', []), f'{section_key}')

                    section_items.append(f"""
                    <div class="news-item">
                        <h3>{item.get('title', '')}</h3>
                        <p>{format_text(item.get('description', ''))} {item_urls}</p>
                        <div class="tags">
                            {', '.join(
                                f'<span class="tag">{tag}</span>' for tag in item.get('tags', []))}
                        </div>
                    </div>
                    """)

                if section_items:
                    html_sections.append(f"""
                    <div class="section" id="{section_key}">
                        <h2 class="section-header">{section_header}</h2>
                        <div class="section-content">
                            {''.join(section_items)}
                        </div>
                    </div>
                    """)

        # Add closing summary section
        if 'closing_summary' in content and content['closing_summary']:
            html_sections.append(f"""
            <div class="section" id="closing_summary">
                <h2 class="section-header">9. LOKAORÐ:</h2>
                <div class="section-content">
                    <p>{format_text(content['closing_summary'])}</p>
                </div>
            </div>
            """)

        # Add signature section
        html_sections.append(f"""
        <div class="section signature-section">
            <p class="signature">Fréttabréfið er skrifað af gervigreind frá OpenAI. Gæti innihaldið ofsjónir. Verkefni forritað af Jasoni Andra Gíslasyni.</p>
            <p class="unsubscribe"><a href="https://docs.google.com/forms/d/e/1FAIpQLSfHWhr9DmTtrtazcCANt-yjpxoAmF9ZEj_lQKZmCwQAqQNZzw/viewform?usp=header">Hætta áskrift á fréttabréfinu</a></p>
        </div>
        """)

        # Combine sections
        html_content = '\n'.join(html_sections)

        # Create the full HTML email template with updated styles
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: 'Segoe UI', Arial, sans-serif;
                    line-height: 1.6;
                    color: #2c3e50;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f8f9fa;
                }}
                .section {{
                    background-color: #ffffff;
                    border-radius: 12px;
                    padding: 25px;
                    margin-bottom: 25px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    transition: transform 0.2s ease;
                }}
                .section:hover {{
                    transform: translateY(-2px);
                }}
                .title-section {{
                    text-align: center;
                    background: linear-gradient(135deg, #2c3e50, #3498db);
                    color: white;
                    padding: 40px 20px;
                    border-radius: 12px;
                }}
                .newsletter-title {{
                    font-size: 2.4em;
                    margin: 0;
                    font-weight: bold;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
                }}
                .newsletter-date {{
                    font-size: 1.2em;
                    margin: 10px 0 0;
                    opacity: 0.9;
                }}
                .main-headline {{
                    color: #2c3e50;
                    font-size: 1.8em;
                    margin-top: 0;
                    margin-bottom: 20px;
                    padding-bottom: 15px;
                    border-bottom: 3px solid #3498db;
                }}
                .section-header {{
                    color: #2c3e50;
                    font-size: 1.5em;
                    margin-top: 0;
                    margin-bottom: 20px;
                    padding-bottom: 10px;
                    border-bottom: 2px solid #e9ecef;
                }}
                .section-content {{
                    color: #444;
                }}
                .news-item {{
                    margin-bottom: 25px;
                    padding-bottom: 20px;
                    border-bottom: 1px solid #e9ecef;
                }}
                .news-item:last-child {{
                    border-bottom: none;
                }}
                .news-item h3 {{
                    color: #2c3e50;
                    margin-top: 0;
                    margin-bottom: 12px;
                    font-size: 1.3em;
                }}
                .impact {{
                    font-style: italic;
                    color: #666;
                    margin: 12px 0;
                    padding: 10px;
                    background-color: #f8f9fa;
                    border-left: 4px solid #3498db;
                }}
                .tags {{
                    margin-top: 12px;
                }}
                .tag {{
                    display: inline-block;
                    background-color: #e9ecef;
                    color: #495057;
                    padding: 4px 10px;
                    border-radius: 20px;
                    margin-right: 8px;
                    font-size: 0.9em;
                    transition: background-color 0.2s ease;
                }}
                .tag:hover {{
                    background-color: #3498db;
                    color: white;
                }}
                .signature-section {{
                    text-align: center;
                    font-style: italic;
                    color: #666;
                    border-top: 2px solid #e9ecef;
                    margin-top: 40px;
                    padding-top: 20px;
                }}
                .signature {{
                    margin: 0;
                    font-size: 0.9em;
                }}
                .unsubscribe {{
                    margin-top: 15px;
                    font-size: 0.9em;
                }}
                .unsubscribe a {{
                    color: #666;
                    text-decoration: none;
                    border-bottom: 1px solid #666;
                    transition: color 0.2s ease;
                }}
                .unsubscribe a:hover {{
                    color: #3498db;
                    border-bottom-color: #3498db;
                }}
                .footnote-link {{
                    color: #3498db;
                    text-decoration: none;
                    font-size: 0.8em;
                    vertical-align: super;
                    position: relative;
                }}
                .footnote-link:hover {{
                    color: #2980b9;
                }}
                .footnote-link[data-tooltip]:hover::after {{
                    content: attr(data-tooltip);
                    position: absolute;
                    bottom: 100%;
                    left: 50%;
                    transform: translateX(-50%);
                    padding: 8px;
                    background-color: #2c3e50;
                    color: white;
                    border-radius: 4px;
                    font-size: 0.9em;
                    white-space: nowrap;
                    z-index: 1000;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                }}
                .toc-section {{
                    background-color: #f8f9fa;
                    border: 1px solid #e9ecef;
                }}
                .toc-container {{
                    display: flex;
                    flex-wrap: wrap;
                    gap: 10px;
                    padding: 10px;
                }}
                .toc-item {{
                    display: inline-block;
                    padding: 8px 15px;
                    background-color: #e9ecef;
                    color: #2c3e50;
                    text-decoration: none;
                    border-radius: 20px;
                    font-size: 0.9em;
                    transition: all 0.2s ease;
                }}
                .toc-item:hover {{
                    background-color: #3498db;
                    color: white;
                    transform: translateY(-2px);
                }}
                strong {{
                    color: #2c3e50;
                    font-weight: 600;
                }}
                p {{
                    margin-bottom: 15px;
                    line-height: 1.6;
                }}
                @media only screen and (max-width: 600px) {{
                    body {{
                        padding: 10px;
                    }}
                    .section {{
                        padding: 15px;
                    }}
                    .newsletter-title {{
                        font-size: 1.8em;
                    }}
                    .main-headline {{
                        font-size: 1.5em;
                    }}
                    .section-header {{
                        font-size: 1.3em;
                    }}
                    .footnote-link[data-tooltip]:hover::after {{
                        display: none;
                    }}
                    .toc-container {{
                        flex-direction: column;
                    }}
                    .toc-item {{
                        width: 100%;
                        text-align: center;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="newsletter-container">
                {html_content}
            </div>
        </body>
        </html>
        """

        logger.info("Newsletter HTML formatting completed")
        return html_template

    except Exception as e:
        logger.error(f"Error formatting newsletter HTML: {str(e)}")
        return None


def save_formatted_newsletter(html_content: str, date_str: str) -> Path:
    """Save the formatted newsletter to an HTML file.

    Args:
        html_content (str): The HTML content to save.
        date_str (str): The date string to use in the filename.

    Returns:
        Path: The path to the saved HTML file.
    """
    try:
        logger.debug(f"Saving formatted newsletter for {date_str}")

        # Create base formatted newsletters directory
        formatted_dir = Path('src/outputs/formatted_newsletters/daily_morning')
        formatted_dir.mkdir(parents=True, exist_ok=True)

        # Generate base filename
        base_filename = f'daily_morning_{date_str}'
        output_file = formatted_dir / f'{base_filename}.html'

        # Save the HTML content
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"Saved formatted newsletter to: {output_file}")
        return output_file

    except Exception as e:
        logger.error(f"Error saving formatted newsletter: {str(e)}")
        return None


def run_formatter(args) -> None:
    """Run the newsletter formatter.

    Args:
        args: Command line arguments.
    """
    logger.info("Starting newsletter formatting...")

    try:
        logger.info(f"Formatting newsletter...")

        # Read the newsletter content
        content, date_str, input_file = read_newsletter_file(
            date_str=args.date,
            file_path=args.file
        )

        # Log the content structure for debugging
        logger.info(f"Processing newsletter from {input_file}")
        logger.info(f"Content keys: {list(content.keys())}")

        # Format the content as HTML
        html_content = format_newsletter_html(content)

        # Save the formatted newsletter
        output_file = save_formatted_newsletter(
            html_content, date_str)
        logger.info(f"Formatted newsletter saved to: {output_file}")

    except FileNotFoundError as e:
        logger.error(
            f"File not found for newsletter: {str(e)}")
    except ValueError as e:
        logger.error(
            f"Error formatting newsletter: {str(e)}")
    except Exception as e:
        logger.error(
            f"Unexpected error formatting newsletter: {str(e)}")
        logger.exception("Detailed error information:")


def main():
    """Main function to run the newsletter formatter."""
    parser = argparse.ArgumentParser(
        description='Format newsletter content into HTML')
    parser.add_argument('--date', help='Date of the newsletter (YYYY-MM-DD)')
    parser.add_argument('--file', help='Path to the newsletter file')
    parser.add_argument('--increment', type=int, default=1,
                        help='Increment number for the newsletter file (e.g., 1 for newsletter_2025-05-10_1.txt)')
    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        run_formatter(args)
    except Exception as e:
        logger.error(f"Error running formatter: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
