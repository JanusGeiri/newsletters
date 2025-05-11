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
import logging
from typing import Tuple, List, Dict, Optional
from newsletter_schemas import NewsletterType, NEWSLETTER_SCHEMAS

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('newsletter_generation.log'),
        logging.StreamHandler()
    ]
)

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Time ranges for different newsletter types
TIME_RANGES = {
    NewsletterType.DAILY_MORNING: None,  # Uses previous day's articles
    NewsletterType.DAILY_NOON: {
        "start": "03:00",
        "end": "11:30"
    },
    NewsletterType.DAILY_EVENING: {
        "start": "03:00",
        "end": "17:30"
    },
    NewsletterType.WEEKLY: None  # Uses past week's articles
}


def load_news_data(date_str: Optional[str] = None,
                   sample_size: int = 10,
                   newsletter_type: NewsletterType = NewsletterType.DAILY_MORNING) -> Tuple[List[Dict], str]:
    """Load news data based on the newsletter type and date.

    Args:
        date_str (str, optional): Date string in YYYY-MM-DD format. Defaults to None.
        sample_size (int, optional): Number of articles to randomly sample. Defaults to 10.
        newsletter_type (NewsletterType): Type of newsletter to generate.

    Returns:c
        Tuple[List[Dict], str]: Tuple containing the articles and the date string used.
    """
    news_dir = Path('outputs/news/json')

    # Determine the date range based on newsletter type
    if newsletter_type == NewsletterType.WEEKLY:
        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')
        current_date = datetime.strptime(date_str, '%Y-%m-%d')
        start_date = current_date - timedelta(days=7)
        date_str = start_date.strftime('%Y-%m-%d')
    elif newsletter_type == NewsletterType.DAILY_MORNING:
        if not date_str:
            date_str = (datetime.now() - timedelta(days=1)
                        ).strftime('%Y-%m-%d')
    else:
        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')

    # Get all relevant files based on newsletter type
    if newsletter_type == NewsletterType.WEEKLY:
        files = []
        current_date = datetime.strptime(date_str, '%Y-%m-%d')
        for i in range(7):
            check_date = current_date + timedelta(days=i)
            file_path = news_dir / \
                f'news_articles_{check_date.strftime("%Y-%m-%d")}.json'
            if file_path.exists():
                files.append(file_path)
    else:
        file_path = news_dir / f'news_articles_{date_str}.json'
        if not file_path.exists():
            raise FileNotFoundError(
                f"No news article file found for date: {date_str}")
        files = [file_path]

    # Load and combine articles from all relevant files
    all_articles = []
    for file_path in files:
        with open(file_path, 'r', encoding='utf-8') as f:
            articles = json.load(f)
            all_articles.extend(articles)

    # Filter articles based on time range if specified
    if newsletter_type in [NewsletterType.DAILY_NOON, NewsletterType.DAILY_EVENING]:
        time_range = TIME_RANGES[newsletter_type]
        filtered_articles = []
        for article in all_articles:
            article_time = datetime.strptime(
                article['article_date'], '%Y-%m-%d %H:%M:%S').time()
            start_time = datetime.strptime(time_range['start'], '%H:%M').time()
            end_time = datetime.strptime(time_range['end'], '%H:%M').time()

            if start_time <= article_time <= end_time:
                filtered_articles.append(article)
        all_articles = filtered_articles

    # Take a random sample of articles if needed
    if len(all_articles) > sample_size:
        all_articles = random.sample(all_articles, sample_size)

    return all_articles, date_str


def format_articles_for_prompt(articles: List[Dict], newsletter_type: NewsletterType) -> str:
    """Format articles into a string for the prompt.

    Args:
        articles (List[Dict]): List of articles to format.
        newsletter_type (NewsletterType): Type of newsletter being generated.

    Returns:
        str: Formatted articles string.
    """
    if not articles:
        return "No articles available."

    # For weekly newsletters, show date range
    if newsletter_type == NewsletterType.WEEKLY:
        dates = [datetime.strptime(article['article_date'], '%Y-%m-%d %H:%M:%S').date()
                 for article in articles]
        min_date = min(dates)
        max_date = max(dates)
        date_header = f"Date Range: {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}"
    else:
        # For daily newsletters, show single date
        date_header = f"Date: {articles[0]['article_date']}"

    formatted_articles = [date_header]

    # Group articles by date for weekly newsletters
    if newsletter_type == NewsletterType.WEEKLY:
        articles_by_date = {}
        for article in articles:
            date = datetime.strptime(
                article['article_date'], '%Y-%m-%d %H:%M:%S').date()
            if date not in articles_by_date:
                articles_by_date[date] = []
            articles_by_date[date].append(article)

        # Sort dates
        sorted_dates = sorted(articles_by_date.keys())

        # Format articles by date
        for date in sorted_dates:
            formatted_articles.append(f"\n=== {date.strftime('%Y-%m-%d')} ===")
            for article in articles_by_date[date]:
                formatted_article = f"""
Title: {article['article_title']}
Source: {article['article_source']}
Content: {article['article_text']}
"""
                formatted_articles.append(formatted_article)
    else:
        # Format daily newsletters as before
        for article in articles:
            formatted_article = f"""
Title: {article['article_title']}
Source: {article['article_source']}
Content: {article['article_text']}
"""
            formatted_articles.append(formatted_article)

    return "\n".join(formatted_articles)


def get_previous_newsletters(newsletter_type: NewsletterType, date_str: str, num_previous: int = 2) -> str:
    """Get the content of previous newsletters for context.

    Args:
        newsletter_type (NewsletterType): Type of newsletter being generated.
        date_str (str): Current date string in YYYY-MM-DD format.
        num_previous (int, optional): Number of previous newsletters to fetch. Defaults to 2.

    Returns:
        str: Content of previous newsletters or a message if none found.
    """
    newsletters_dir = Path('outputs/newsletters') / newsletter_type.value

    if not newsletters_dir.exists():
        return "NO PREVIOUS NEWSLETTERS FOUND"

    # Get all newsletter files for this type
    files = list(newsletters_dir.glob(f'{newsletter_type.value}_*.json'))
    if not files:
        return "NO PREVIOUS NEWSLETTERS FOUND"

    # Sort files by date (newest first)
    files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

    # Get the most recent files
    previous_newsletters = []
    for file in files[:num_previous]:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()  # Read raw content as string
                # Extract date from filename
                date = file.stem.split('_')[1]
                previous_newsletters.append(
                    f"=== Newsletter from {date} ===\n{content}\n")
        except Exception as e:
            print(
                f"Warning: Could not read previous newsletter {file}: {str(e)}")

    if not previous_newsletters:
        return "NO PREVIOUS NEWSLETTERS FOUND"

    # Add extra newline between newsletters
    return "\n\n".join(previous_newsletters)


def load_prompt_template(newsletter_type: NewsletterType, date_str: str, formated_articles: str) -> str:
    """Load the appropriate newsletter prompt template based on type.

    Args:
        newsletter_type (NewsletterType): Type of newsletter to generate.
        date_str (str): Date string in YYYY-MM-DD format.
        formated_articles (str): Formated articles string.
    Returns:
        str: The prompt template for the specified newsletter type.
    """
    template_map = {
        NewsletterType.DAILY_MORNING: 'prompts/newsletter_daily_morning.txt',
        NewsletterType.DAILY_NOON: 'prompts/newsletter_daily_noon.txt',
        NewsletterType.DAILY_EVENING: 'prompts/newsletter_daily_evening.txt',
        NewsletterType.WEEKLY: 'prompts/newsletter_weekly.txt'
    }

    # Load base template
    with open('prompts/base_newsletter_prompt.txt', 'r', encoding='utf-8') as f:
        base_template = f.read()

    # Load specific template
    template_path = template_map[newsletter_type]
    with open(template_path, 'r', encoding='utf-8') as f:
        specific_template = f.read()

    # Prepare date variables based on newsletter type
    if newsletter_type == NewsletterType.WEEKLY:
        current_date = datetime.strptime(date_str, '%Y-%m-%d')
        start_date = current_date - timedelta(days=7)
        end_date = current_date - timedelta(days=1)
        date_vars = {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        }
    else:
        # For daily newsletters, use the same date
        date_vars = {'date': date_str}

    # Split the specific template into its components
    template_parts = specific_template.split('{newsletter_title}')
    if len(template_parts) != 2:
        raise ValueError(
            f"Invalid template format in {template_path}: missing newsletter_title")

    intro_part = template_parts[0]
    remaining_parts = template_parts[1].split('{newsletter_sections}')
    if len(remaining_parts) != 2:
        raise ValueError(
            f"Invalid template format in {template_path}: missing newsletter_sections")

    title_part = remaining_parts[0]
    remaining_parts = remaining_parts[1].split(
        '{newsletter_specific_instructions}')
    if len(remaining_parts) != 2:
        raise ValueError(
            f"Invalid template format in {template_path}: missing newsletter_specific_instructions")

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
            f"Missing required date variable in template {template_path}: {str(e)}. Required variables: {list(date_vars.keys())}")

    # Get previous newsletters
    previous_newsletters = get_previous_newsletters(newsletter_type, date_str)

    # Format the base template with the combined content
    try:
        total_formatted = base_template.format(
            newsletter_specific_intro=formatted_intro,
            newsletter_title=formatted_title,
            newsletter_sections=formatted_sections,
            newsletter_specific_instructions=formatted_instructions,
            previous_newsletters=previous_newsletters,
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


def generate_newsletter(articles: List[Dict], newsletter_type: NewsletterType, date_str: str) -> str:
    """Generate a newsletter using the OpenAI API.

    Args:
        articles (List[Dict]): List of articles to include in the newsletter.
        newsletter_type (NewsletterType): Type of newsletter to generate.
        date_str (str): Date string in YYYY-MM-DD format.

    Returns:
        str: The generated newsletter content in JSON format.
    """
    # Format articles for the prompt
    formatted_articles = format_articles_for_prompt(articles, newsletter_type)
    # Load and format the prompt template
    prompt = load_prompt_template(
        newsletter_type, date_str, formatted_articles)

    # Estimate tokens in the prompt
    prompt_tokens = estimate_tokens(prompt)
    logging.info(f"Estimated prompt tokens: {prompt_tokens}")

    # Get the schema for this newsletter type
    schema = NEWSLETTER_SCHEMAS[newsletter_type]

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
        temperature=0.01,
        max_tokens=25000
    )

    # Log the response tokens
    completion_tokens = response.usage.completion_tokens
    total_tokens = response.usage.total_tokens
    logging.info(f"Completion tokens: {completion_tokens}")
    logging.info(f"Total tokens used: {total_tokens}")

    # Return the JSON response directly
    output = response.choices[0].message.content
    return output


def save_newsletter(newsletter_content: str, date_str: str, newsletter_type: NewsletterType) -> Path:
    """Save the generated newsletter to a JSON file with incremental suffix if needed.

    Args:
        newsletter_content (str): The content of the newsletter to save.
        date_str (str): The date string to use in the filename.
        newsletter_type (NewsletterType): Type of newsletter being saved.

    Returns:
        Path: The path to the saved newsletter file.
    """
    if not date_str:
        raise ValueError("Date string is required to save the newsletter")

    # Create base newsletters directory
    newsletters_dir = Path('outputs/newsletters')

    # Create type-specific subdirectory
    type_dir = newsletters_dir / newsletter_type.value
    type_dir.mkdir(parents=True, exist_ok=True)

    # Generate base filename with type prefix
    base_filename = f'{newsletter_type.value}_{date_str}'
    output_file = type_dir / f'{base_filename}.json'

    # Check if file exists and add incremental suffix if needed
    counter = 1
    while output_file.exists():
        output_file = type_dir / f'{base_filename}_{counter}.json'
        counter += 1

    # Parse the newsletter content back to JSON since it was converted to string
    newsletter_json = json.loads(newsletter_content)
    # Save the newsletter as JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(newsletter_json, f, ensure_ascii=False, indent=2)

    return output_file


def main():
    parser = argparse.ArgumentParser(
        description='Generate newsletters from news articles')
    parser.add_argument(
        '--date', help='Date of the news articles (YYYY-MM-DD)')
    parser.add_argument('--sample-size', type=int, default=200,
                        help='Number of articles to sample')
    parser.add_argument('--type', type=str, required=True,
                        choices=[t.value for t in NewsletterType],
                        help='Type of newsletter to generate')
    args = parser.parse_args()

    try:
        # Convert string type to enum
        newsletter_type = NewsletterType(args.type)

        # Load news data
        articles, date_str = load_news_data(
            args.date,
            args.sample_size,
            newsletter_type
        )

        # Generate newsletter
        newsletter_content = generate_newsletter(
            articles, newsletter_type, date_str)

        # Save newsletter
        output_file = save_newsletter(
            newsletter_content, date_str, newsletter_type)
        print(f"Newsletter generated successfully and saved to: {output_file}")

    except Exception as e:
        print(f"Error generating newsletter: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
