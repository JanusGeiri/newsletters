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
            "description": "A short description of the news item (2-4 paragraphs)"
        },
        "tags": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "description": "Tags categorizing the news item"
        }
    },
    "required": ["title", "description", "tags"],
    "additionalProperties": False
}

# Extended schema for news items with dates (used in weekly newsletters)
KEY_EVENT_ITEM_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {
            "type": "string",
            "description": "The headline of the news item"
        },
        "tldr": {
            "type": "string",
            "description": "A short summary of the news item (TLDR)"
        },
        "description": {
            "type": "string",
            "description": "A detailed summary of the news item (5-7 paragraphs). Make sure to include all the details of the news item. If it is long, make sure to break it into paragraphs."
        },
        "tags": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "description": "Tags categorizing the news item"
        }
    },
    "required": ["title", "description", "tldr", "tags"],
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
                    "items": KEY_EVENT_ITEM_SCHEMA,
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
            "required": ["main_headline", "summary", "key_events", "domestic_news", "foreign_news", "business", "famous_people", "sports", "arts", "science", "closing_summary"],
            "additionalProperties": False
        },
        "strict": True
    }
}
