# Automated Newsletter Generation System

This project is an automated system for generating and sending newsletters based on news articles. It includes functionality for scraping news, generating newsletters using AI, formatting them, and sending them to subscribers. The system also maintains a static website for newsletter archives and subscriptions.

## Features

- News scraping and aggregation from multiple sources (visir, mbl, vb, ruv)
- AI-powered newsletter generation using GPT-4
- Article grouping and similarity analysis
- Impact analysis for news items
- Automated newsletter formatting with responsive HTML templates
- Newsletter distribution via email
- Unsubscribe management
- Index page generation for newsletter archives
- Automated daily newsletter generation via GitHub Actions
- Static website for newsletter archives and subscriptions

## Project Overview

The system follows a modular pipeline architecture where each component processes data and passes it to the next stage. The pipeline ensures data consistency and allows for easy testing and modification of individual components. Each stage produces structured JSON outputs that are consumed by the next stage, making the system highly maintainable and extensible.

### Core Components

1. **News Scraping (`nl_scraper/`)**
   - `MasterScraper`: Orchestrates scraping from multiple news sources
   - Supports multiple news sources (visir, mbl, vb, ruv)
   - Outputs article data in a structured JSON format containing:
     - Article metadata (title, date, source)
     - Article content
     - URLs and references
     - Source-specific attributes
     - Timestamps and processing information
     - Article lemmas (extracted using Greynir, an Icelandic NLP parser)
       - Text is cleaned and processed to extract lemmas
       - Common words and stopwords are filtered out
       - Lemmas are used for article similarity comparison

2. **Article Processing (`nl_article_processor/`)**
   - `ArticleGroupProcessor`: Groups similar articles using various similarity strategies
     - Uses lemmas extracted from article text to compare articles
     - Currently uses Jaccard similarity as the default strategy
     - Supports pluggable similarity strategies:
       - Jaccard: Basic set-based similarity
       - Enhanced Jaccard: TF-IDF weighted similarity
       - LSA (Latent Semantic Analysis): Dimensionality reduction for better semantic matching
     - Multiple strategies are being tested and evaluated for better accuracy
     - Each strategy can be configured with different parameters
   - Processes and organizes articles into meaningful groups
   - Outputs structured article groups with:
     - Group metadata and statistics
     - Member articles and their relationships
     - Similarity scores and confidence metrics

3. **Newsletter Generation (`nl_generator/`)**
   - `NewsletterGenerator`: Main orchestrator for newsletter creation
   - `PromptGenerator`: Creates AI prompts for newsletter generation
   - `RawNLGenerator`: Generates raw newsletter content using GPT-4.1-mini
   - `NLProcessor`: Processes newsletters with article matching and impact generation
     - Matches AI-generated news items with original article groups
     - Ensures correct URL attribution for each news item
     - Maintains data consistency between generated content and source articles
     - Adds impact analysis to news items
   - Outputs unprocessed and processed newsletters

4. **Newsletter Formatting (`nl_formatter/`)**
   - `NewsletterFormatter`: Formats newsletters for email and web display
   - `NewsletterTemplate`: Provides HTML templates and styling
   - Outputs formatted HTML newsletters

5. **Newsletter Distribution (`nl_sender/`)**
   - `NewsletterSender`: Handles email distribution
   - `SubscriberManager`: Manages subscriber list and unsubscribes
   - Sends newsletters to active subscribers

### Website Components

1. **Landing Page (`index.html`)**
   - Static HTML page serving as the main entry point
   - Features:
     - Newsletter subscription form
     - Latest newsletter preview
     - Archive of all past newsletters
     - Unsubscribe form
   - Styled with responsive CSS for all devices

2. **Index Updates (`update_index.py`)**
   - Automatically updates the website's index page
   - Runs as part of the newsletter generation pipeline
   - Updates:
     - Latest newsletter link
     - Newsletter archive list
     - Maintains chronological order of newsletters
   - Ensures the website stays current with new content

## Data Flow

1. **News Collection**
   - Scrapers collect news from multiple sources
   - Articles are stored in raw format
   - Data is validated and cleaned
   - Timestamps and metadata are added
   - Articles are deduplicated
   - Source-specific processing is applied

2. **Article Processing**
   - Articles are grouped by similarity
   - Groups are analyzed for impact and relevance
   - Similarity scores are calculated
   - Cross-source relationships are identified
   - Group metadata is enriched

3. **Newsletter Generation**
   - AI generates newsletter content based on article groups
   - Content is processed with article matching
   - Impact analysis is added to news items
   - Content is structured into sections
   - Headlines and summaries are generated
   - Cross-references are added

4. **Formatting and Distribution**
   - Newsletter is formatted into responsive HTML
   - Email is sent to active subscribers
   - Web version is archived
   - Analytics are collected
   - Delivery status is tracked
   - Unsubscribe requests are processed

## Prerequisites

- Python 3.8 or higher
- OpenAI API key
- Gmail account with app password for automation
- Google Sheets API access (for subscriber management)

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd newsletters
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the root directory with the following variables:
```
OPENAI_API_KEY=your_openai_api_key
NEWSLETTER_EMAIL=your_gmail_address
NEWSLETTER_PASSWORD=your_16_character_gmail_app_password
GOOGLE_SHEET_ID=your_google_sheet_id
GOOGLE_SHEET_ID_UNSUB=your_unsubscribe_sheet_id
GOOGLE_SHEET_API_KEY=your_google_sheet_api_key
private_key_id=your_private_key_id
private_key=your_private_key
```

## Usage

### Running the Newsletter System

1. To run the complete newsletter generation and sending process:
```bash
python src/scripts/automate_newsletter.py
```

2. To run individual components:

```bash
# Scrape news articles
python src/scripts/nl_scraper/master_scraper.py

# Generate a newsletter
python src/scripts/nl_generator/newsletter_generator.py --date YYYY-MM-DD

# Format a newsletter
python src/scripts/nl_formatter/newsletter_formatter.py --date YYYY-MM-DD

# Send a newsletter
python src/scripts/nl_sender/send_newsletter.py --date YYYY-MM-DD

# Process unsubscribes
python src/scripts/nl_sender/process_unsubscribes.py
```

### Development Mode

The system supports a development mode that can be enabled in `automate_newsletter.py`. This mode:
- Uses a fixed date for testing
- Allows selective running of components
- Disables email sending
- Provides detailed logging

## Automation

The system is configured to automatically generate and send newsletters daily using GitHub Actions. The `automate_newsletter.py` script handles this automation process.

### Website Automation

- The website is automatically updated via GitHub Actions
- Updates are triggered by:
  - New newsletter generation
  - Direct pushes to the repository
- The process ensures that:
  - The latest newsletter is always prominently displayed
  - The archive is kept up to date
  - All links remain functional
  - The website stays in sync with the newsletter generation pipeline

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 