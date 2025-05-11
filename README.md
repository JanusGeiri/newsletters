# News Summary Generator

This project automatically generates daily news summaries from various Icelandic news sources. It scrapes news articles, processes them using OpenAI's GPT-4, and formats them into a newsletter.

## Features

- Scrapes news from multiple Icelandic sources (Visir, MBL, Vb, RUV)
- Generates summaries using OpenAI's GPT-4
- Supports multiple newsletter types (daily morning, daily noon, daily evening, weekly)
- Formats newsletters in HTML with a clean, modern design
- Sends newsletters to subscribers via email
- Web interface to view past newsletters
- Automatic index page updates with reverse chronological ordering

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd news_summary
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your configuration:
```env
OPENAI_API_KEY=your_openai_api_key
NEWSLETTER_EMAIL=your_email@gmail.com
NEWSLETTER_PASSWORD=your_app_specific_password
```

## Usage

### Command Line Interface

The main script (`main.py`) supports several modes of operation:

```bash
# Full pipeline (scrape, generate, and format)
python main.py --mode full_pipeline --daily-morning --date 2024-03-15

# Generate and format without scraping
python main.py --mode generate_and_format --daily-morning --date 2024-03-15

# Scrape only
python main.py --mode scrape_only --date 2024-03-15

# Generate only
python main.py --mode generate_only --daily-morning --date 2024-03-15

# Format only
python main.py --mode format_only --daily-morning --date 2024-03-15
```

### Newsletter Types

- `--daily-morning`: Morning newsletter (previous day's news)
- `--daily-noon`: Noon newsletter (morning news)
- `--daily-evening`: Evening newsletter (afternoon news)
- `--weekly`: Weekly summary
- `--all-types`: Generate all types of newsletters

### Additional Options

```bash
# Specify news sources
python main.py --mode full_pipeline --sources visir mbl vb ruv

# Set sample size for articles
python main.py --mode full_pipeline --sample-size 100

# Enable verbose logging
python main.py --mode full_pipeline --verbose
```

### Sending Newsletters

To send newsletters to subscribers:

```bash
# Send latest newsletter
python send_newsletter.py

# Send newsletter for specific date
python send_newsletter.py --date 2024-03-15

# Send specific newsletter file
python send_newsletter.py --file daily_morning_2024-03-15.html
```

### Web Interface

To start the web interface:

```bash
# Start the simple HTTP server
python serve.py
```

The web interface will be available at `http://localhost:8000`

### Updating the Index Page

The index page is automatically updated to show the latest newsletters in reverse chronological order:

```bash
# Update index.html with latest newsletter links
python update_index.py
```

This script:
- Scans the `outputs/formatted_newsletters/daily_morning` directory for newsletter files
- Updates the latest newsletter section with the most recent newsletter
- Updates the newsletter list with all newsletters sorted by date (newest first)
- Maintains a clean, organized display of all past newsletters

## Project Structure

```
news_summary/
├── main.py                 # Main script for newsletter generation
├── news_scraper.py         # News scraping functionality
├── newsletter_generator.py # Newsletter generation using GPT-4
├── newsletter_formatter.py # HTML formatting for newsletters
├── newsletter_schemas.py   # Newsletter type definitions and schemas
├── send_newsletter.py      # Email sending functionality
├── update_index.py         # Index page update functionality
├── serve.py               # Simple HTTP server for the web interface
├── automate_newsletter.py # Automation script for scheduled runs
├── index.html             # Main web interface template
├── static/                # Static assets
│   └── css/              # CSS stylesheets
├── prompts/              # GPT prompt templates
├── outputs/              # Generated content
│   ├── news/            # Scraped news articles
│   ├── newsletters/     # Raw generated newsletters
│   └── formatted_newsletters/  # Formatted HTML newsletters
│       └── daily_morning/     # Morning newsletters
├── logs/                # Log files
└── instance/           # Instance-specific files
```

## Automation

The project includes an automation script (`automate_newsletter.py`) that can be scheduled to run daily:

```bash
# Run automation script
python automate_newsletter.py
```

To schedule it with cron (runs at 3 AM):
```bash
0 3 * * * cd /path/to/news_summary && python automate_newsletter.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 