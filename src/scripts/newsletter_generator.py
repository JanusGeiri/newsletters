#!/usr/bin/env python3
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
import random
import argparse
import sys
import tiktoken
from typing import List, Dict, Optional, Tuple
from logger_config import get_logger
from newsletter_schemas import DAILY_MORNING_SCHEMA
import requests

# Get logger
logger = get_logger('newsletter_generator')

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


def load_news_data(date_str=None, sample_size=200):
    """Load news data from JSON file."""
    try:
        logger.debug(
            f"Loading news data for date: {date_str}")

        # Find the most recent news file if date not specified
        if not date_str:
            news_dir = Path("src/outputs/news/json")
            files = list(news_dir.glob("news_articles_*.json"))
            if not files:
                logger.error("No news article files found")
                return None, None

            # Get the most recent file
            latest_file = max(files, key=lambda x: x.stat().st_mtime)
            date_str = latest_file.stem.split('_')[-1]
            logger.debug(f"Using most recent file: {latest_file}")

        # Load the articles
        file_path = Path("src/outputs/news/json") / \
            f"news_articles_{date_str}.json"
        if not file_path.exists():
            logger.error(f"No news file found for date: {date_str}")
            return None, None

        with open(file_path, 'r', encoding='utf-8') as f:
            articles = json.load(f)

        logger.info(f"Loaded {len(articles)} articles from {file_path}")
        return articles, date_str

    except Exception as e:
        logger.error(f"Error loading news data: {str(e)}")
        return None, None


def format_articles_for_prompt(articles: List[Dict]) -> str:
    """Format articles into a string for the prompt.

    Args:
        articles (List[Dict]): List of articles to format.

    Returns:
        str: Formatted articles string.
    """
    if not articles:
        return "No articles available."

    date_header = f"Date: {articles[0]['article_date']}"

    formatted_articles = [date_header]

    # Create a new shuffled list of articles
    shuffled_articles = random.sample(articles, len(articles))

    for article in shuffled_articles:
        formatted_article = f"""
Title: {article['article_title']}
Source: {article['article_source']}
Content: {article['article_text']}
"""
        formatted_articles.append(formatted_article)

    return "\n".join(formatted_articles)


def load_prompt_template(date_str: str, formated_articles: str) -> str:
    """Load the appropriate newsletter prompt template based on type.

    Args:
        date_str (str): Date string in YYYY-MM-DD format.
        formated_articles (str): Formated articles string.
    Returns:
        str: The prompt template for the specified newsletter type.
    """

    # Load base template
    with open('src/prompts/base_newsletter_prompt.txt', 'r', encoding='utf-8') as f:
        base_template = f.read()

    # Load specific template
    with open('src/prompts/newsletter_daily_morning.txt', 'r', encoding='utf-8') as f:
        specific_template = f.read()
    date_vars = {'date': date_str}

    # Split the specific template into its components
    template_parts = specific_template.split('{newsletter_title}')
    if len(template_parts) != 2:
        raise ValueError(
            f"Invalid template format: missing newsletter_title")

    intro_part = template_parts[0]
    remaining_parts = template_parts[1].split('{newsletter_sections}')
    if len(remaining_parts) != 2:
        raise ValueError(
            f"Invalid template format: missing newsletter_sections")

    title_part = remaining_parts[0]
    remaining_parts = remaining_parts[1].split(
        '{newsletter_specific_instructions}')
    if len(remaining_parts) != 2:
        raise ValueError(
            f"Invalid template format: missing newsletter_specific_instructions")

    sections_part = remaining_parts[0]
    instructions_part = remaining_parts[1]

    # Format each part
    try:
        # Intro part doesn't need date formatting
        formatted_intro = intro_part

        # Format title part with date variables
        formatted_title = title_part.format(**date_vars)

        # Sections part doesn't need date formatting
        formatted_sections = sections_part

        # Instructions part doesn't need date formatting
        formatted_instructions = instructions_part

    except KeyError as e:
        raise ValueError(
            f"Missing required date variable in template: {str(e)}. Required variables: {list(date_vars.keys())}")

    # Format the base template with the combined content
    try:
        total_formatted = base_template.format(
            newsletter_specific_intro=formatted_intro,
            newsletter_title=formatted_title,
            newsletter_sections=formatted_sections,
            newsletter_specific_instructions=formatted_instructions,
            articles=formated_articles  # Add placeholder for articles
        )
        return total_formatted
    except KeyError as e:
        raise ValueError(
            f"Missing required variable in base template: {str(e)}")


def estimate_tokens(text: str, model: str = "gpt-4") -> int:
    """Estimate the number of tokens in a text string.

    Args:
        text (str): The text to estimate tokens for
        model (str): The model to use for token estimation

    Returns:
        int: Estimated number of tokens
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except KeyError:
        # Fallback to cl100k_base encoding if model not found
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))


def generate_impact(text: str, urls: List[str] = None) -> Tuple[str, List[str]]:
    """Generate impact analysis using GPT-4 with web search.

    Args:
        text (str): The text to analyze (news item or summary)
        urls (List[str], optional): List of URLs related to the text. Defaults to None.

    Returns:
        Tuple[str, List[str]]: The generated impact analysis and list of citation URLs
    """
    try:
        # Load the impact prompt template
        with open('src/prompts/impact_prompt.txt', 'r', encoding='utf-8') as f:
            prompt_template = f.read()

        # Format URLs for the prompt
        urls_text = "\n".join(urls) if urls else "No URLs provided"

        # Format the prompt
        prompt = prompt_template.format(
            news_item=text,
            urls=urls_text
        )

        # Call OpenAI API with web search enabled
        response = client.chat.completions.create(
            model="gpt-4o-search-preview",
            messages=[
                {"role": "system", "content": prompt}
            ],
            web_search_options={
                "user_location": {
                    "type": "approximate",
                    "approximate": {
                        "country": "IS",
                        "city": "Reykjavík",
                        "region": "Reykjavík",
                    }
                },
                "search_context_size": "high"
            }
        )
        return response.choices[0].message.content.strip(), [annotation.url_citation.url for annotation in response.choices[0].message.annotations]

    except Exception as e:
        logger.error(f"Error generating impact: {str(e)}")
        return "Impact analysis unavailable", []


def validate_url(url: str) -> bool:
    """Validate if a URL is properly formatted and accessible.

    Args:
        url (str): The URL to validate

    Returns:
        bool: True if URL is valid and accessible, False otherwise
    """
    try:
        # Basic URL format validation
        if not url or not isinstance(url, str):
            return False

        # Check if URL starts with http/https
        if not url.startswith(('http://', 'https://')):
            return False

        # Try to make a HEAD request to check if URL is accessible
        response = requests.head(url, timeout=5, allow_redirects=True)
        return response.status_code < 400

    except Exception:
        return False


def clean_urls_in_newsletter(newsletter_json: Dict) -> Dict:
    """Clean and validate URLs in the newsletter JSON.

    Args:
        newsletter_json (Dict): The newsletter JSON to clean

    Returns:
        Dict: Newsletter JSON with cleaned URLs
    """
    try:
        logger.info("Starting URL cleaning process")
        total_urls = 0
        valid_urls = 0

        def clean_url_list(urls: List[str]) -> List[str]:
            """Clean a list of URLs by removing duplicates and invalid URLs."""
            if not urls:
                return []
            # Remove duplicates while preserving order
            seen = set()
            unique_urls = [
                url for url in urls if url not in seen and not seen.add(url)]
            # Filter valid URLs
            return [url for url in unique_urls if validate_url(url)]

        # Clean summary URLs
        if 'summary_urls' in newsletter_json:
            original_count = len(newsletter_json['summary_urls'])
            newsletter_json['summary_urls'] = clean_url_list(
                newsletter_json['summary_urls'])
            valid_count = len(newsletter_json['summary_urls'])
            total_urls += original_count
            valid_urls += valid_count
            logger.info(
                f"Summary URLs: {valid_count}/{original_count} valid URLs")

        # Clean summary impact URLs
        if 'summary_impact_urls' in newsletter_json:
            original_count = len(newsletter_json['summary_impact_urls'])
            newsletter_json['summary_impact_urls'] = clean_url_list(
                newsletter_json['summary_impact_urls'])
            valid_count = len(newsletter_json['summary_impact_urls'])
            total_urls += original_count
            valid_urls += valid_count
            logger.info(
                f"Summary impact URLs: {valid_count}/{original_count} valid URLs")

        # Clean URLs in key events
        if 'key_events' in newsletter_json:
            key_events_total = 0
            key_events_valid = 0
            for i, event in enumerate(newsletter_json['key_events']):
                if 'urls' in event:
                    original_count = len(event['urls'])
                    event['urls'] = clean_url_list(event['urls'])
                    valid_count = len(event['urls'])
                    key_events_total += original_count
                    key_events_valid += valid_count
                    logger.debug(
                        f"Key event {i+1} URLs: {valid_count}/{original_count} valid URLs")

                if 'impact_urls' in event:
                    original_count = len(event['impact_urls'])
                    event['impact_urls'] = clean_url_list(event['impact_urls'])
                    valid_count = len(event['impact_urls'])
                    key_events_total += original_count
                    key_events_valid += valid_count
                    logger.debug(
                        f"Key event {i+1} impact URLs: {valid_count}/{original_count} valid URLs")

            total_urls += key_events_total
            valid_urls += key_events_valid
            logger.info(
                f"Key events URLs: {key_events_valid}/{key_events_total} valid URLs")

        # Clean URLs in other sections
        sections = ['domestic_news', 'foreign_news', 'business',
                    'famous_people', 'sports', 'arts', 'science']

        for section in sections:
            if section in newsletter_json:
                section_total = 0
                section_valid = 0
                for i, item in enumerate(newsletter_json[section]):
                    if 'urls' in item:
                        original_count = len(item['urls'])
                        item['urls'] = clean_url_list(item['urls'])
                        valid_count = len(item['urls'])
                        section_total += original_count
                        section_valid += valid_count
                        logger.debug(
                            f"{section} item {i+1} URLs: {valid_count}/{original_count} valid URLs")

                total_urls += section_total
                valid_urls += section_valid
                logger.info(
                    f"{section} URLs: {section_valid}/{section_total} valid URLs")

        logger.info(
            f"URL cleaning completed. Total: {valid_urls}/{total_urls} valid URLs ({valid_urls/total_urls*100:.1f}% valid)")
        return newsletter_json

    except Exception as e:
        logger.error(f"Error cleaning URLs in newsletter: {str(e)}")
        return newsletter_json


def update_newsletter_with_impacts(newsletter_json: Dict) -> Dict:
    """Update the newsletter JSON with generated impacts.

    Args:
        newsletter_json (Dict): The original newsletter JSON

    Returns:
        Dict: Updated newsletter JSON with impacts
    """
    try:
        # Generate impact for summary
        newsletter_json['summary_impact'] = generate_impact(
            newsletter_json['summary'],
            newsletter_json.get('summary_urls', [])
        )

        # Generate impacts for key events
        for event in newsletter_json['key_events']:
            event['impact'] = generate_impact(
                f"Title: {event['title']}\nDescription: {event['description']}",
                event.get('urls', [])
            )

        return newsletter_json

    except Exception as e:
        logger.error(f"Error updating newsletter with impacts: {str(e)}")
        return newsletter_json


def generate_newsletter(articles: List[Dict], date_str: str) -> str:
    """Generate a newsletter using the OpenAI API.

    Args:
        articles (List[Dict]): List of articles to include in the newsletter.
        date_str (str): Date string in YYYY-MM-DD format.

    Returns:
        str: The generated newsletter content in JSON format.
    """
    try:
        logger.info(f"Generating newsletter for {date_str}")
        logger.debug(f"Processing {len(articles)} articles")

        # Format articles for the prompt
        formatted_articles = format_articles_for_prompt(articles)
        # Load and format the prompt template
        prompt = load_prompt_template(date_str, formatted_articles)

        # Estimate tokens in the prompt
        prompt_tokens = estimate_tokens(prompt)
        logger.info(f"Estimated prompt tokens: {prompt_tokens}")

        # Get the schema for this newsletter type
        schema = DAILY_MORNING_SCHEMA

        # Call the OpenAI API
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": prompt}
            ],
            response_format={
                "type": "json_schema",
                "json_schema": schema.get("json_schema")
            },
            temperature=0.01
        )

        # Log the response tokens
        completion_tokens = response.usage.completion_tokens
        total_tokens = response.usage.total_tokens
        logger.info(f"Completion tokens: {completion_tokens}")
        logger.info(f"Total tokens used: {total_tokens}")

        # Get the initial newsletter content
        newsletter_json = json.loads(response.choices[0].message.content)

        # Convert back to string
        output = json.dumps(newsletter_json)
        logger.info("Newsletter generation completed")
        return output

    except Exception as e:
        logger.error(f"Error generating newsletter: {str(e)}")
        return None


def save_newsletter(newsletter_content: str, date_str: str) -> Path:
    """Save the generated newsletter to a JSON file with incremental suffix if needed.

    Args:
        newsletter_content (str): The content of the newsletter to save.
        date_str (str): The date string to use in the filename.

    Returns:
        Path: The path to the saved newsletter file.
    """
    try:
        logger.debug(f"Saving newsletter for {date_str}")

        if not date_str:
            raise ValueError("Date string is required to save the newsletter")

        # Create base newsletters directory
        newsletters_dir = Path('src/outputs/newsletters/daily_morning')

        # Create type-specific subdirectory
        type_dir = newsletters_dir
        type_dir.mkdir(parents=True, exist_ok=True)

        # Generate base filename with type prefix
        base_filename = f'daily_morning_{date_str}'
        output_file = type_dir / f'{base_filename}.json'

        # Parse the newsletter content back to JSON since it was converted to string
        newsletter_json = json.loads(newsletter_content)
        # Save the newsletter as JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(newsletter_json, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved newsletter to: {output_file}")
        return output_file

    except Exception as e:
        logger.error(f"Error saving newsletter: {str(e)}")
        return None


def insert_impacts(newsletter_file: Path) -> bool:
    """Insert impact analysis into an existing newsletter file.

    Args:
        newsletter_file (Path): Path to the newsletter file to update

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info(f"Inserting impacts into newsletter: {newsletter_file}")

        if not newsletter_file.exists():
            logger.error(f"Newsletter file not found: {newsletter_file}")
            return False

        # Load the existing newsletter
        with open(newsletter_file, 'r', encoding='utf-8') as f:
            newsletter_json = json.load(f)

        # Generate impact for summary
        logger.info("Generating summary impact")
        impact_text, impact_urls = generate_impact(
            newsletter_json['summary'],
            newsletter_json.get('summary_urls', [])
        )
        newsletter_json['summary_impact'] = impact_text
        newsletter_json['summary_impact_urls'] = impact_urls

        # Generate impacts for key events
        logger.info("Generating impacts for key events")
        for event in newsletter_json['key_events']:
            logger.info(f"Generating impact for key event: {event['title']}")
            impact_text, impact_urls = generate_impact(
                f"Title: {event['title']}\nDescription: {event['description']}",
                event.get('urls', [])
            )
            event['impact'] = impact_text
            event['impact_urls'] = impact_urls

        # Save the updated newsletter
        with open(newsletter_file, 'w', encoding='utf-8') as f:
            json.dump(newsletter_json, f, ensure_ascii=False, indent=2)

        logger.info(
            f"Successfully inserted impacts into newsletter: {newsletter_file}")
        return True

    except Exception as e:
        logger.error(f"Error inserting impacts into newsletter: {str(e)}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Generate newsletters from news articles')
    parser.add_argument(
        '--date', help='Date of the news articles (YYYY-MM-DD)')
    parser.add_argument('--sample-size', type=int, default=200,
                        help='Number of articles to sample')
    parser.add_argument('--add-impacts', action='store_true',
                        help='Add impact analysis to an existing newsletter')
    args = parser.parse_args()

    try:
        logger.info("Starting newsletter generation")
        logger.debug(f"Arguments: {args}")

        if args.add_impacts:
            if not args.date:
                logger.error("Date is required when adding impacts")
                return
            success = insert_impacts(
                Path(f'src/outputs/newsletters/daily_morning/{args.date}.json'))
            if success:
                print(
                    f"Successfully added impacts to newsletter for {args.date}")
            else:
                print(f"Failed to add impacts to newsletter for {args.date}")
            return

        # Load news data
        articles, date_str = load_news_data(
            args.date,
            args.sample_size
        )

        # Generate newsletter
        newsletter_content = generate_newsletter(
            articles, date_str)

        # Save newsletter
        output_file = save_newsletter(
            newsletter_content, date_str)
        print(f"Newsletter generated successfully and saved to: {output_file}")

        logger.info("Newsletter generation completed successfully")

    except Exception as e:
        logger.error(f"Error in newsletter generation: {str(e)}")
        raise


if __name__ == "__main__":
    main()
