import os
from pathlib import Path
from datetime import datetime, timedelta
import re
import argparse
import sys
import json
import logging
from typing import Tuple, Optional, List
from newsletter_generator import NewsletterType

# Set up logging
logger = logging.getLogger(__name__)


def get_date_from_filename(filename):
    """Extract date and increment from newsletter filename."""
    match = re.search(r'newsletter_(\d{4}-\d{2}-\d{2})(?:_(\d+))?', filename)
    if match:
        date_str = match.group(1)
        increment = int(match.group(2)) if match.group(2) else 1
        return date_str, increment
    return None, None


def read_newsletter_file(date_str: Optional[str] = None, file_path: Optional[str] = None, increment: int = 1, newsletter_type: Optional[NewsletterType] = None) -> Tuple[dict, str, Path]:
    """Read a newsletter file and return its content.

    Args:
        date_str (Optional[str]): Date string in YYYY-MM-DD format. If None, use current date.
        file_path (Optional[str]): Path to the newsletter file. If None, find the most recent file.
        increment (int): Increment number for the newsletter file.
        newsletter_type (Optional[NewsletterType]): Type of newsletter to read.

    Returns:
        Tuple[dict, str, Path]: Tuple containing the newsletter content as a dict, date string, and input file path.
    """
    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')

    # Create base newsletters directory
    newsletters_dir = Path('outputs/newsletters')

    if file_path:
        input_file = Path(file_path)
    else:
        if not newsletter_type:
            raise ValueError(
                "Newsletter type must be specified when no file path is provided")

        # Create type-specific subdirectory
        type_dir = newsletters_dir / newsletter_type.value
        if not type_dir.exists():
            raise FileNotFoundError(
                f"No directory found for newsletter type: {newsletter_type.value}")

        # First try to find a file matching the exact date
        base_filename = f'{newsletter_type.value}_{date_str}'
        if increment > 1:
            base_filename = f'{base_filename}_{increment}'

        input_file = type_dir / f'{base_filename}.json'

        # If no file exists for the specified date, find the most recent file
        if not input_file.exists():
            files = list(type_dir.glob(f'{newsletter_type.value}_*.json'))
            if not files:
                raise FileNotFoundError(
                    f"No newsletter files found for type: {newsletter_type.value}")

            # Sort files by modification time (newest first)
            files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            # If date is specified, try to find the most recent file before or on that date
            if date_str:
                target_date = datetime.strptime(date_str, '%Y-%m-%d')
                for file in files:
                    # Get date part from filename
                    file_date_str = file.stem.split('_')[1]
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
        logger.error(f"Error reading newsletter file {input_file}: {str(e)}")
        raise


def format_newsletter_html(content):
    """Convert JSON newsletter content to HTML format."""
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

    # Get newsletter type from content
    newsletter_type = content.get('newsletter_type', 'daily_morning')

    # Format title based on newsletter type
    if newsletter_type == 'weekly':
        date_from = content.get('date_from', '')
        date_to = content.get('date_to', '')
        title = f"VIKULEGT FRÉTTABRÉF ({date_from} - {date_to})"
    else:
        date = content.get('date', '')
        if newsletter_type == 'daily_morning':
            title = f"FRÉTTIR GÆRDAGSINS ({date})"
        elif newsletter_type == 'daily_noon':
            title = f"FRÉTTIR DAGSINS - HÁDEGI ({date})"
        elif newsletter_type == 'daily_evening':
            title = f"FRÉTTIR DAGSINS - KVÖLD ({date})"
        else:
            title = f"FRÉTTIR DAGSINS ({date})"

    # Start building HTML sections
    html_sections = []

    # Add title section
    html_sections.append(f"""
    <div class="section title-section">
        <h1 class="newsletter-title">{title}</h1>
    </div>
    """)

    # Add main headline and summary section
    html_sections.append(f"""
    <div class="section">
        <h2 class="main-headline">{content.get('main_headline', '')}</h2>
        <div class="section-content">
            <p>{format_text(content.get('summary', ''))}</p>
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

            key_events_html.append(f"""
            <div class="news-item">
                <h3>{event.get('title', '')}</h3>
                <p>{format_text(event.get('description', ''))}</p>
                <p class="impact"><strong>Áhrif:</strong> {format_text(event.get('impact', ''))}</p>
                <div class="tags">
                    {', '.join(f'<span class="tag">{tag}</span>' for tag in event.get('tags', []))}
                </div>
            </div>
            """)

        if key_events_html:
            html_sections.append(f"""
            <div class="section">
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

                section_items.append(f"""
                <div class="news-item">
                    <h3>{item.get('title', '')}</h3>
                    <p>{format_text(item.get('description', ''))}</p>
                    <p class="impact"><strong>Áhrif:</strong> {format_text(item.get('impact', ''))}</p>
                    <div class="tags">
                        {', '.join(f'<span class="tag">{tag}</span>' for tag in item.get('tags', []))}
                    </div>
                </div>
                """)

            if section_items:
                html_sections.append(f"""
                <div class="section">
                    <h2 class="section-header">{section_header}</h2>
                    <div class="section-content">
                        {''.join(section_items)}
                    </div>
                </div>
                """)

    # Add closing summary section
    if 'closing_summary' in content and content['closing_summary']:
        html_sections.append(f"""
        <div class="section">
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
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f9f9f9;
            }}
            .section {{
                background-color: #ffffff;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .title-section {{
                text-align: center;
                background-color: #2c3e50;
                color: white;
                padding: 30px 20px;
            }}
            .newsletter-title {{
                font-size: 2.2em;
                margin: 0;
                font-weight: bold;
            }}
            .main-headline {{
                color: #2c3e50;
                font-size: 1.8em;
                margin-top: 0;
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 2px solid #eee;
            }}
            .section-header {{
                color: #2c3e50;
                font-size: 1.5em;
                margin-top: 0;
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 2px solid #eee;
            }}
            .section-content {{
                color: #444;
            }}
            .news-item {{
                margin-bottom: 25px;
                padding-bottom: 15px;
                border-bottom: 1px solid #eee;
            }}
            .news-item:last-child {{
                border-bottom: none;
            }}
            .news-item h3 {{
                color: #2c3e50;
                margin-top: 0;
                margin-bottom: 10px;
            }}
            .impact {{
                font-style: italic;
                color: #666;
                margin: 10px 0;
            }}
            .tags {{
                margin-top: 10px;
            }}
            .tag {{
                display: inline-block;
                background-color: #e9ecef;
                color: #495057;
                padding: 3px 8px;
                border-radius: 4px;
                margin-right: 5px;
                font-size: 0.9em;
            }}
            .signature-section {{
                text-align: center;
                font-style: italic;
                color: #666;
                border-top: 1px solid #eee;
                margin-top: 40px;
            }}
            .signature {{
                margin: 0;
                font-size: 0.9em;
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

    return html_template


def save_formatted_newsletter(html_content: str, date_str: str, newsletter_type: NewsletterType) -> Path:
    """Save the formatted newsletter to an HTML file.

    Args:
        html_content (str): The HTML content to save.
        date_str (str): The date string to use in the filename.
        newsletter_type (NewsletterType): Type of newsletter being saved.

    Returns:
        Path: The path to the saved HTML file.
    """
    # Create base formatted newsletters directory
    formatted_dir = Path('outputs/formatted_newsletters')

    # Create type-specific subdirectory
    type_dir = formatted_dir / newsletter_type.value
    type_dir.mkdir(parents=True, exist_ok=True)

    # Generate base filename with type prefix
    base_filename = f'{newsletter_type.value}_{date_str}'
    output_file = type_dir / f'{base_filename}.html'

    # Check if file exists and add incremental suffix if needed
    counter = 1
    while output_file.exists():
        output_file = type_dir / f'{base_filename}_{counter}.html'
        counter += 1

    # Save the HTML content
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    return output_file


def get_newsletter_types(args) -> List[NewsletterType]:
    """Get the newsletter types to process based on command line arguments.

    Args:
        args: Command line arguments.

    Returns:
        List[NewsletterType]: List of newsletter types to process.
    """
    if args.type:
        return [NewsletterType(args.type)]
    return list(NewsletterType)


def run_formatter(args) -> None:
    """Run the newsletter formatter.

    Args:
        args: Command line arguments.
    """
    logger.info("Starting newsletter formatting...")

    # Get newsletter types to process
    newsletter_types = get_newsletter_types(args)
    if not newsletter_types:
        logger.error("No newsletter types specified")
        return

    for newsletter_type in newsletter_types:
        try:
            logger.info(f"Formatting {newsletter_type.value} newsletter...")

            # Read the newsletter content
            content, date_str, input_file = read_newsletter_file(
                date_str=args.date,
                file_path=args.file,
                increment=args.increment,
                newsletter_type=newsletter_type
            )

            # Log the content structure for debugging
            logger.info(f"Processing newsletter from {input_file}")
            logger.info(f"Content keys: {list(content.keys())}")

            # Format the content as HTML
            html_content = format_newsletter_html(content)

            # Save the formatted newsletter
            output_file = save_formatted_newsletter(
                html_content, date_str, newsletter_type)
            logger.info(f"Formatted newsletter saved to: {output_file}")

        except FileNotFoundError as e:
            logger.error(
                f"File not found for {newsletter_type.value} newsletter: {str(e)}")
        except ValueError as e:
            logger.error(
                f"Error formatting {newsletter_type.value} newsletter: {str(e)}")
        except Exception as e:
            logger.error(
                f"Unexpected error formatting {newsletter_type.value} newsletter: {str(e)}")
            logger.exception("Detailed error information:")


def main():
    """Main function to run the newsletter formatter."""
    parser = argparse.ArgumentParser(
        description='Format newsletter content into HTML')
    parser.add_argument('--date', help='Date of the newsletter (YYYY-MM-DD)')
    parser.add_argument('--file', help='Path to the newsletter file')
    parser.add_argument('--increment', type=int, default=1,
                        help='Increment number for the newsletter file (e.g., 1 for newsletter_2025-05-10_1.txt)')
    parser.add_argument('--type', help='Type of newsletter to process',
                        choices=[t.value for t in NewsletterType])
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
