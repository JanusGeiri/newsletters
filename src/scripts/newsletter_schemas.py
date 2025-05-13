from enum import Enum
from typing import Dict


class NewsletterType(Enum):
    DAILY_MORNING = "daily_morning"  # Previous day's news (early morning)
    DAILY_NOON = "daily_noon"        # Current day 3AM-11:30AM
    DAILY_EVENING = "daily_evening"  # Current day 3AM-5:30PM
    WEEKLY = "weekly"                # Past week's news (Monday morning)


# Base schema for news items
NEWS_ITEM_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {
            "type": "string",
            "description": "The headline of the news item"
        },
        "description": {
            "type": "string",
            "description": "A short description of the news item (1-2 sentences)"
        },
        "impact": {
            "type": "string",
            "description": "Analysis of the impact and context of the news"
        },
        "tags": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "description": "Tags categorizing the news item"
        }
    },
    "required": ["title", "description", "impact", "tags"],
    "additionalProperties": False
}

# Extended schema for news items with dates (used in weekly newsletters)
EXTENDED_NEWS_ITEM_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {
            "type": "string",
            "description": "The headline of the news item"
        },
        "description": {
            "type": "string",
            "description": "A detailed description of the news item (1-2 paragraphs)"
        },
        "impact": {
            "type": "string",
            "description": "Analysis of the impact and context of the news (1-2 sentences)"
        },
        "tags": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "description": "Tags categorizing the news item"
        },
    },
    "required": ["title", "description", "impact", "tags"],
    "additionalProperties": False
}

# Schema for daily morning newsletter
DAILY_MORNING_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "DailyMorningNewsletter",
        "schema": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "The date of the newsletter in YYYY-MM-DD format"
                },
                "main_headline": {
                    "type": "string",
                    "description": "The main headline of the newsletter (AÐALFRÉTT). Try to avoid sports or entertainment news for the headline, only if its something that is very big."
                },
                "summary": {
                    "type": "string",
                    "description": "A comprehensive summary of the day's events (SAMANTEKT)"
                },
                "key_events": {
                    "type": "array",
                    "items": EXTENDED_NEWS_ITEM_SCHEMA,
                    "description": "The most important news stories of the day (MIKILVÆGUSTU FRÉTTIRNAR)"
                },
                "domestic_news": {
                    "type": "array",
                    "items": NEWS_ITEM_SCHEMA,
                    "description": "Domestic news stories (INNLENT)"
                },
                "foreign_news": {
                    "type": "array",
                    "items": NEWS_ITEM_SCHEMA,
                    "description": "Foreign news stories (ERLENT)"
                },
                "business": {
                    "type": "array",
                    "items": NEWS_ITEM_SCHEMA,
                    "description": "Business and economic news (VIÐSKIPTI)"
                },
                "famous_people": {
                    "type": "array",
                    "items": NEWS_ITEM_SCHEMA,
                    "description": "News about notable personalities (FRÆGA FÓLKIÐ)"
                },
                "sports": {
                    "type": "array",
                    "items": NEWS_ITEM_SCHEMA,
                    "description": "Sports news and updates (ÍÞRÓTTIR)"
                },
                "arts": {
                    "type": "array",
                    "items": NEWS_ITEM_SCHEMA,
                    "description": "Arts and culture news (LISTIR)"
                },
                "science": {
                    "type": "array",
                    "items": NEWS_ITEM_SCHEMA,
                    "description": "Science and technology news (VÍSINDI)"
                },
                "closing_summary": {
                    "type": "string",
                    "description": "A closing summary of the day's events and preview of tomorrow (LOKAORÐ)"
                }
            },
            "required": ["date", "main_headline", "summary", "key_events", "domestic_news", "foreign_news", "business", "famous_people", "sports", "arts", "science", "closing_summary"],
            "additionalProperties": False
        },
        "strict": True
    }
}

# Schema for daily noon newsletter
DAILY_NOON_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "DailyNoonNewsletter",
        "schema": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "The date of the newsletter in YYYY-MM-DD format"
                },
                "main_headline": {
                    "type": "string",
                    "description": "The main headline of the newsletter (AÐALFRÉTT). Try to avoid sports or entertainment news for the headline, only if its something that is very big."
                },
                "summary": {
                    "type": "string",
                    "description": "A concise summary of the morning's events (SAMANTEKT)"
                },
                "key_events": {
                    "type": "array",
                    "items": NEWS_ITEM_SCHEMA,
                    "description": "The most important morning news stories (MIKILVÆGUSTU FRÉTTIRNAR)"
                },
                "domestic_news": {
                    "type": "array",
                    "items": NEWS_ITEM_SCHEMA,
                    "description": "Domestic news from the morning (INNLENT)"
                },
                "foreign_news": {
                    "type": "array",
                    "items": NEWS_ITEM_SCHEMA,
                    "description": "Foreign news from the morning (ERLENT)"
                },
                "business": {
                    "type": "array",
                    "items": NEWS_ITEM_SCHEMA,
                    "description": "Business news from the morning (VIÐSKIPTI)"
                },
                "closing_summary": {
                    "type": "string",
                    "description": "A brief summary of morning developments and afternoon preview (LOKAORÐ)"
                }
            },
            "required": ["date", "main_headline", "summary", "key_events", "domestic_news", "foreign_news", "business", "closing_summary"],
            "additionalProperties": False
        },
        "strict": True
    }
}

# Schema for daily evening newsletter
DAILY_EVENING_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "DailyEveningNewsletter",
        "schema": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "The date of the newsletter in YYYY-MM-DD format"
                },
                "main_headline": {
                    "type": "string",
                    "description": "The main headline of the newsletter (AÐALFRÉTT). Try to avoid sports or entertainment news for the headline, only if its something that is very big."
                },
                "summary": {
                    "type": "string",
                    "description": "A summary of the day's events (SAMANTEKT)"
                },
                "key_events": {
                    "type": "array",
                    "items": NEWS_ITEM_SCHEMA,
                    "description": "The most important stories of the day (MIKILVÆGUSTU FRÉTTIRNAR)"
                },
                "domestic_news": {
                    "type": "array",
                    "items": NEWS_ITEM_SCHEMA,
                    "description": "Domestic news from the day (INNLENT)"
                },
                "foreign_news": {
                    "type": "array",
                    "items": NEWS_ITEM_SCHEMA,
                    "description": "Foreign news from the day (ERLENT)"
                },
                "business": {
                    "type": "array",
                    "items": NEWS_ITEM_SCHEMA,
                    "description": "Business news from the day (VIÐSKIPTI)"
                },
                "closing_summary": {
                    "type": "string",
                    "description": "A summary of the day's developments and tomorrow's preview (LOKAORÐ)"
                }
            },
            "required": ["date", "main_headline", "summary", "key_events", "domestic_news", "foreign_news", "business", "closing_summary"],
            "additionalProperties": False
        },
        "strict": True
    }
}

# Schema for weekly newsletter
WEEKLY_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "WeeklyNewsletter",
        "schema": {
            "type": "object",
            "properties": {
                "date_from": {
                    "type": "string",
                    "description": "The start date of the week in YYYY-MM-DD format"
                },
                "date_to": {
                    "type": "string",
                    "description": "The end date of the week in YYYY-MM-DD format"
                },
                "main_headline": {
                    "type": "string",
                    "description": "The main headline capturing the week's theme (AÐALFRÉTT). Try to avoid sports or entertainment news for the headline, only if its something that is very big."
                },
                "summary": {
                    "type": "string",
                    "description": "A comprehensive summary of the week's events (SAMANTEKT)"
                },
                "key_events": {
                    "type": "array",
                    "items": EXTENDED_NEWS_ITEM_SCHEMA,
                    "description": "The most important news stories of the week (MIKILVÆGUSTU FRÉTTIRNAR)"
                },
                "domestic_news": {
                    "type": "array",
                    "items": EXTENDED_NEWS_ITEM_SCHEMA,
                    "description": "Domestic news from the week (INNLENT)"
                },
                "foreign_news": {
                    "type": "array",
                    "items": EXTENDED_NEWS_ITEM_SCHEMA,
                    "description": "Foreign news from the week (ERLENT)"
                },
                "business": {
                    "type": "array",
                    "items": EXTENDED_NEWS_ITEM_SCHEMA,
                    "description": "Business news from the week (VIÐSKIPTI)"
                },
                "famous_people": {
                    "type": "array",
                    "items": EXTENDED_NEWS_ITEM_SCHEMA,
                    "description": "Notable personalities in the news (FRÆGA FÓLKIÐ)"
                },
                "sports": {
                    "type": "array",
                    "items": EXTENDED_NEWS_ITEM_SCHEMA,
                    "description": "Sports news from the week (ÍÞRÓTTIR)"
                },
                "arts": {
                    "type": "array",
                    "items": EXTENDED_NEWS_ITEM_SCHEMA,
                    "description": "Arts and culture news (LISTIR)"
                },
                "science": {
                    "type": "array",
                    "items": EXTENDED_NEWS_ITEM_SCHEMA,
                    "description": "Science and technology news (VÍSINDI)"
                },
                "closing_summary": {
                    "type": "string",
                    "description": "A comprehensive summary of the week's themes and next week's preview (LOKAORÐ)"
                }
            },
            "required": ["date_from", "date_to", "main_headline", "summary", "key_events", "domestic_news", "foreign_news", "business", "famous_people", "sports", "arts", "science", "closing_summary"],
            "additionalProperties": False
        },
        "strict": True
    }
}

# Mapping of newsletter types to their schemas
NEWSLETTER_SCHEMAS: Dict[NewsletterType, dict] = {
    NewsletterType.DAILY_MORNING: DAILY_MORNING_SCHEMA,
    NewsletterType.DAILY_NOON: DAILY_NOON_SCHEMA,
    NewsletterType.DAILY_EVENING: DAILY_EVENING_SCHEMA,
    NewsletterType.WEEKLY: WEEKLY_SCHEMA
}
