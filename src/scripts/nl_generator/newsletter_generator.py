#!/usr/bin/env python3
"""
Newsletter generator module for creating newsletters from news articles.
"""
import json
import random
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional

import argparse
import requests
from dotenv import load_dotenv
import tiktoken
from openai import OpenAI

from nl_utils.logger_config import get_logger
from nl_utils.newsletter_schemas import DAILY_MORNING_SCHEMA
from nl_utils import (
    load_news_articles,
    save_newsletter_json,
    load_text_file,
    load_json_file,
    save_json_file
)

# Load environment variables
load_dotenv()


class NewsletterGenerator:
    """Class for generating and processing newsletters."""

    def __init__(self, debug_mode: bool = False):
        """Initialize the NewsletterGenerator.

        Args:
            debug_mode (bool): Whether to run in debug mode.
        """
        self.logger = get_logger('newsletter_generator')
        self.debug_mode = debug_mode
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    def load_news_data(self, date_str: Optional[str] = None, sample_size: int = 200) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """Load news data from JSON file.

        Args:
            date_str (Optional[str]): Date string in YYYY-MM-DD format.
            sample_size (int): Number of articles to sample.

        Returns:
            Tuple[Optional[List[Dict]], Optional[str]]: Articles and date string.
        """
        try:
            self.logger.debug("Loading news data for date: %s", date_str)
            articles, date_str = load_news_articles(date_str)
            return articles, date_str
        except Exception as e:
            self.logger.error("Error loading news data: %s", str(e))
            return None, None

    def format_articles_for_prompt(self, articles: List[Dict]) -> str:
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
        shuffled_articles = random.sample(articles, len(articles))

        for article in shuffled_articles:
            formatted_article = f"""
Title: {article['article_title']}
Source: {article['article_source']}
Content: {article['article_text']}
"""
            formatted_articles.append(formatted_article)

        return "\n".join(formatted_articles)

    def load_prompt_template(self, date_str: str, formated_articles: str) -> str:
        """Load the appropriate newsletter prompt template based on type.

        Args:
            date_str (str): Date string in YYYY-MM-DD format.
            formated_articles (str): Formated articles string.

        Returns:
            str: The prompt template for the specified newsletter type.
        """
        try:
            base_template = load_text_file(
                'src/prompts/base_newsletter_prompt.txt')
            specific_template = load_text_file(
                'src/prompts/newsletter_daily_morning.txt')
            date_vars = {'date': date_str}

            template_parts = specific_template.split('{newsletter_title}')
            if len(template_parts) != 2:
                raise ValueError(
                    "Invalid template format: missing newsletter_title")

            intro_part = template_parts[0]
            remaining_parts = template_parts[1].split('{newsletter_sections}')
            if len(remaining_parts) != 2:
                raise ValueError(
                    "Invalid template format: missing newsletter_sections")

            title_part = remaining_parts[0]
            remaining_parts = remaining_parts[1].split(
                '{newsletter_specific_instructions}')
            if len(remaining_parts) != 2:
                raise ValueError(
                    "Invalid template format: missing newsletter_specific_instructions")

            sections_part = remaining_parts[0]
            instructions_part = remaining_parts[1]

            formatted_intro = intro_part
            formatted_title = title_part.format(**date_vars)
            formatted_sections = sections_part
            formatted_instructions = instructions_part

            total_formatted = base_template.format(
                newsletter_specific_intro=formatted_intro,
                newsletter_title=formatted_title,
                newsletter_sections=formatted_sections,
                newsletter_specific_instructions=formatted_instructions,
                articles=formated_articles
            )
            return total_formatted

        except Exception as e:
            self.logger.error("Error loading prompt template: %s", str(e))
            raise

    def estimate_tokens(self, text: str, model: str = "gpt-4") -> int:
        """Estimate the number of tokens in a text string.

        Args:
            text (str): The text to estimate tokens for.
            model (str): The model to use for token estimation.

        Returns:
            int: Estimated number of tokens.
        """
        try:
            encoding = tiktoken.encoding_for_model(model)
            return len(encoding.encode(text))
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))

    def generate_impact(self, text: str, urls: List[str] = None) -> Tuple[str, List[str]]:
        """Generate impact analysis using GPT-4 with web search.

        Args:
            text (str): The text to analyze (news item or summary).
            urls (List[str], optional): List of URLs related to the text.

        Returns:
            Tuple[str, List[str]]: The generated impact analysis and list of citation URLs.
        """
        try:
            prompt_template = load_text_file('src/prompts/impact_prompt.txt')
            urls_text = "\n".join(urls) if urls else "No URLs provided"
            prompt = prompt_template.format(news_item=text, urls=urls_text)

            response = self.client.chat.completions.create(
                model="gpt-4o-search-preview",
                messages=[{"role": "system", "content": prompt}],
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
            self.logger.error("Error generating impact: %s", str(e))
            return "Impact analysis unavailable", []

    def validate_url(self, url: str) -> bool:
        """Validate if a URL is properly formatted and accessible.

        Args:
            url (str): The URL to validate.

        Returns:
            bool: True if URL is valid and accessible, False otherwise.
        """
        try:
            if not url or not isinstance(url, str):
                return False

            if not url.startswith(('http://', 'https://')):
                return False

            response = requests.head(url, timeout=5, allow_redirects=True)
            return response.status_code < 400

        except Exception:
            return False

    def clean_urls_in_newsletter(self, newsletter_json: Dict) -> Dict:
        """Clean and validate URLs in the newsletter JSON.

        Args:
            newsletter_json (Dict): The newsletter JSON to clean.

        Returns:
            Dict: Newsletter JSON with cleaned URLs.
        """
        try:
            self.logger.info("Starting URL cleaning process")
            total_urls = 0
            valid_urls = 0

            def clean_url_list(urls: List[str]) -> List[str]:
                if not urls:
                    return []
                seen = set()
                unique_urls = [
                    url for url in urls if url not in seen and not seen.add(url)]
                return [url for url in unique_urls if self.validate_url(url)]

            if 'summary_urls' in newsletter_json:
                original_count = len(newsletter_json['summary_urls'])
                newsletter_json['summary_urls'] = clean_url_list(
                    newsletter_json['summary_urls'])
                valid_count = len(newsletter_json['summary_urls'])
                total_urls += original_count
                valid_urls += valid_count
                self.logger.info("Summary URLs: %d/%d valid URLs",
                                 valid_count, original_count)

            if 'summary_impact_urls' in newsletter_json:
                original_count = len(newsletter_json['summary_impact_urls'])
                newsletter_json['summary_impact_urls'] = clean_url_list(
                    newsletter_json['summary_impact_urls'])
                valid_count = len(newsletter_json['summary_impact_urls'])
                total_urls += original_count
                valid_urls += valid_count
                self.logger.info(
                    "Summary impact URLs: %d/%d valid URLs", valid_count, original_count)

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
                        self.logger.debug(
                            "Key event %d URLs: %d/%d valid URLs", i+1, valid_count, original_count)

                    if 'impact_urls' in event:
                        original_count = len(event['impact_urls'])
                        event['impact_urls'] = clean_url_list(
                            event['impact_urls'])
                        valid_count = len(event['impact_urls'])
                        key_events_total += original_count
                        key_events_valid += valid_count
                        self.logger.debug(
                            "Key event %d impact URLs: %d/%d valid URLs", i+1, valid_count, original_count)

                total_urls += key_events_total
                valid_urls += key_events_valid
                self.logger.info("Key events URLs: %d/%d valid URLs",
                                 key_events_valid, key_events_total)

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
                            self.logger.debug(
                                "%s item %d URLs: %d/%d valid URLs", section, i+1, valid_count, original_count)

                    total_urls += section_total
                    valid_urls += section_valid
                    self.logger.info("%s URLs: %d/%d valid URLs",
                                     section, section_valid, section_total)

            self.logger.info("URL cleaning completed. Total: %d/%d valid URLs (%.1f%% valid)",
                             valid_urls, total_urls, valid_urls/total_urls*100 if total_urls > 0 else 0)
            return newsletter_json

        except Exception as e:
            self.logger.error("Error cleaning URLs in newsletter: %s", str(e))
            return newsletter_json

    def update_newsletter_with_impacts(self, newsletter_json: Dict) -> Dict:
        """Update the newsletter JSON with generated impacts.

        Args:
            newsletter_json (Dict): The original newsletter JSON.

        Returns:
            Dict: Updated newsletter JSON with impacts.
        """
        try:
            newsletter_json['summary_impact'] = self.generate_impact(
                newsletter_json['summary'],
                newsletter_json.get('summary_urls', [])
            )

            for event in newsletter_json['key_events']:
                event['impact'] = self.generate_impact(
                    f"Title: {event['title']}\nDescription: {event['description']}",
                    event.get('urls', [])
                )

            return newsletter_json

        except Exception as e:
            self.logger.error(
                "Error updating newsletter with impacts: %s", str(e))
            return newsletter_json

    def generate_newsletter(self, articles: List[Dict], date_str: str) -> Optional[str]:
        """Generate a newsletter using the OpenAI API.

        Args:
            articles (List[Dict]): List of articles to include in the newsletter.
            date_str (str): Date string in YYYY-MM-DD format.

        Returns:
            Optional[str]: The generated newsletter content in JSON format.
        """
        try:
            self.logger.info("Generating newsletter for %s", date_str)
            self.logger.debug("Processing %d articles", len(articles))

            formatted_articles = self.format_articles_for_prompt(articles)
            prompt = self.load_prompt_template(date_str, formatted_articles)
            prompt_tokens = self.estimate_tokens(prompt)
            self.logger.info("Estimated prompt tokens: %d", prompt_tokens)

            schema = DAILY_MORNING_SCHEMA
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{"role": "system", "content": prompt}],
                response_format={
                    "type": "json_schema",
                    "json_schema": schema.get("json_schema")
                },
                temperature=0.01
            )

            completion_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens
            self.logger.info("Completion tokens: %d", completion_tokens)
            self.logger.info("Total tokens used: %d", total_tokens)

            newsletter_json = json.loads(response.choices[0].message.content)
            output = json.dumps(newsletter_json)
            self.logger.info("Newsletter generation completed")
            return output

        except Exception as e:
            self.logger.error("Error generating newsletter: %s", str(e))
            return None

    def save_newsletter(self, newsletter_content: str, date_str: str) -> Optional[Path]:
        """Save the generated newsletter to a JSON file.

        Args:
            newsletter_content (str): The content of the newsletter to save.
            date_str (str): The date string to use in the filename.

        Returns:
            Optional[Path]: The path to the saved newsletter file.
        """
        try:
            self.logger.debug("Saving newsletter for %s", date_str)

            if not date_str:
                raise ValueError(
                    "Date string is required to save the newsletter")

            return save_newsletter_json(newsletter_content, date_str)

        except Exception as e:
            self.logger.error("Error saving newsletter: %s", str(e))
            return None

    def insert_impacts(self, newsletter_file: Path) -> bool:
        """Insert impact analysis into an existing newsletter file.

        Args:
            newsletter_file (Path): Path to the newsletter file to update.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            self.logger.info(
                "Inserting impacts into newsletter: %s", newsletter_file)

            if not newsletter_file.exists():
                self.logger.error(
                    "Newsletter file not found: %s", newsletter_file)
                return False

            newsletter_json = load_json_file(newsletter_file)

            self.logger.info("Generating summary impact")
            impact_text, impact_urls = self.generate_impact(
                newsletter_json['summary'],
                newsletter_json.get('summary_urls', [])
            )
            newsletter_json['summary_impact'] = impact_text
            newsletter_json['summary_impact_urls'] = impact_urls

            self.logger.info("Generating impacts for key events")
            for event in newsletter_json['key_events']:
                self.logger.info(
                    "Generating impact for key event: %s", event['title'])
                impact_text, impact_urls = self.generate_impact(
                    f"Title: {event['title']}\nDescription: {event['description']}",
                    event.get('urls', [])
                )
                event['impact'] = impact_text
                event['impact_urls'] = impact_urls

            save_json_file(newsletter_json, newsletter_file)
            self.logger.info(
                "Successfully inserted impacts into newsletter: %s", newsletter_file)
            return True

        except Exception as e:
            self.logger.error(
                "Error inserting impacts into newsletter: %s", str(e))
            return False

    def run_generator(self, date_str: str, articles: List[Dict], ignore: bool = False) -> Optional[Path]:
        """Run the newsletter generation process.

        Args:
            date_str (str): Date string in YYYY-MM-DD format.
            articles (List[Dict]): List of articles to include in the newsletter.
            ignore (bool): Whether to ignore operations.

        Returns:
            Optional[Path]: Path to the generated newsletter file.
        """
        try:
            if ignore:
                self.logger.info("Ignoring newsletter generation")
                return True

            self.logger.info("Starting newsletter generation for %s", date_str)
            newsletter_content = self.generate_newsletter(articles, date_str)
            if not newsletter_content:
                return None

            output_file = self.save_newsletter(newsletter_content, date_str)
            if not output_file:
                return None

            self.logger.info("Newsletter generation completed successfully")
            return output_file

        except Exception as e:
            self.logger.error("Error in newsletter generation: %s", str(e))
            return None

    def run_url_cleaner(self, date_str: str, ignore: bool = False) -> bool:
        """Run the URL cleaning process.

        Args:
            date_str (str): Date string in YYYY-MM-DD format.
            ignore (bool): Whether to ignore operations.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            if ignore:
                self.logger.info("Ignoring URL cleaning")
                return True

            self.logger.info("Starting URL cleaning process for %s", date_str)
            newsletters_dir = Path('src/outputs/newsletters/daily_morning')
            newsletter_file = newsletters_dir / \
                f'daily_morning_{date_str}.json'

            if not newsletter_file.exists():
                self.logger.error(
                    "No newsletter file found: %s", newsletter_file)
                return False

            with open(newsletter_file, 'r', encoding='utf-8') as f:
                newsletter_json = json.load(f)

            cleaned_newsletter = self.clean_urls_in_newsletter(newsletter_json)
            with open(newsletter_file, 'w', encoding='utf-8') as f:
                json.dump(cleaned_newsletter, f, ensure_ascii=False, indent=2)

            self.logger.info(
                "Successfully cleaned URLs in: %s", newsletter_file)
            return True

        except Exception as e:
            self.logger.error("Error in URL cleaning process: %s", str(e))
            return False

    def run_impacts(self, date_str: str, ignore: bool = False) -> bool:
        """Run the impact insertion process.

        Args:
            date_str (str): Date string in YYYY-MM-DD format.
            ignore (bool): Whether to ignore operations.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            if ignore:
                self.logger.info("Ignoring impact insertion")
                return True

            self.logger.info("Starting impact insertion for %s", date_str)
            newsletters_dir = Path('src/outputs/newsletters/daily_morning')
            newsletter_file = newsletters_dir / \
                f'daily_morning_{date_str}.json'

            if not newsletter_file.exists():
                self.logger.error(
                    "No newsletter file found: %s", newsletter_file)
                return False

            success = self.insert_impacts(newsletter_file)
            if success:
                self.logger.info(
                    "Successfully inserted impacts into: %s", newsletter_file)
            else:
                self.logger.error(
                    "Failed to insert impacts into: %s", newsletter_file)

            return success

        except Exception as e:
            self.logger.error("Error in impact insertion: %s", str(e))
            return False


def main():
    """Main function to run the newsletter generator."""
    parser = argparse.ArgumentParser(
        description='Generate newsletters from news articles')
    parser.add_argument(
        '--date', help='Date of the news articles (YYYY-MM-DD)')
    parser.add_argument('--sample-size', type=int, default=200,
                        help='Number of articles to sample')
    parser.add_argument('--add-impacts', action='store_true',
                        help='Add impact analysis to an existing newsletter')
    parser.add_argument('--ignore', action='store_true',
                        help='Ignore operations')
    args = parser.parse_args()

    try:
        generator = NewsletterGenerator()
        logger = get_logger('newsletter_generator')

        if args.add_impacts:
            if not args.date:
                logger.error("Date is required when adding impacts")
                return
            success = generator.run_impacts(args.date, args.ignore)
            if success:
                print("Successfully added impacts to newsletter for %s", args.date)
            else:
                print("Failed to add impacts to newsletter for %s", args.date)
            return

        articles, date_str = generator.load_news_data(
            args.date, args.sample_size)
        if not articles or not date_str:
            logger.error("Failed to load news data")
            return

        output_file = generator.run_generator(date_str, articles, args.ignore)
        if output_file:
            print("Newsletter generated successfully and saved to: %s", output_file)
        else:
            print("Failed to generate newsletter")

    except Exception as e:
        logger.error("Error in newsletter generation: %s", str(e))
        raise


if __name__ == "__main__":
    main()
