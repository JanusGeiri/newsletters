# Automated Newsletter Generation System

This project is an automated system for generating and sending newsletters based on news articles. It includes functionality for scraping news, generating newsletters using AI, formatting them, and sending them to subscribers.

## Features

- News scraping and aggregation
- AI-powered newsletter generation using GPT-4
- Automated newsletter formatting and sending
- Web interface for viewing newsletters
- Unsubscribe management
- Index page generation for newsletter archives

## Prerequisites

- Python 3.8 or higher
- OpenAI API key
- Google API credentials (for sending emails)

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

4. Set up environment variables: {you also need the gmail and 16 letter gmail automation password in the env NEWSLETTER_EMAIL and NEWSLETTER_PASSWORD}
Create a `.env` file in the root directory with the following variables:
```
OPENAI_API_KEY=your_openai_api_key
```

5. Set up Google API credentials: {slightly wrong, you need to get this from google and then put the private_key and private_key_id in the .env file}
Place your `creds.json` file in the root directory.

## Project Structure

- `news_scraper.py`: Scrapes news articles from various sources
- `newsletter_generator.py`: Generates newsletters using AI
- `newsletter_formatter.py`: Formats newsletters for email and web display
- `send_newsletter.py`: Handles newsletter distribution
- `process_unsubscribes.py`: Manages unsubscribe requests
- `update_index.py`: Updates the index.html file with new newsletters
- `serve.py`: Web server for viewing newsletters {used only for development on the local machine}
- `newsletter_schemas.py`: Defines newsletter types and schemas
- `prompts/`: Contains prompt templates for different newsletter types
- `outputs/`: Stores generated newsletters and news articles
- `logs/`: Contains log files

## Usage {it is missing the two main files, automate_newsletter.py and main.py, automate_newsletter is used by the github actions to automatically run the daily newsletter generation (check this file and see how it runs) and the main.py is the main way to run all the sub files}

### Generating Newsletters

1. Scrape news articles:
```bash
python news_scraper.py
```

2. Generate a newsletter:
```bash
python newsletter_generator.py --type DAILY_MORNING --date YYYY-MM-DD
```

Available newsletter types:
- `DAILY_MORNING`
- `DAILY_NOON`
- `DAILY_EVENING`
- `WEEKLY`

### Sending Newsletters

To send a generated newsletter:
```bash
python send_newsletter.py --type DAILY_MORNING --date YYYY-MM-DD
```

### Viewing Newsletters

Start the web server:
```bash
python serve.py
```

Then visit `http://localhost:5000` in your browser.

### Processing Unsubscribes

To process unsubscribe requests:
```bash
python process_unsubscribes.py
```

## Automation

The `automate_newsletter.py` script can be used to automate the entire newsletter generation and sending process. It can be scheduled using cron jobs or similar task schedulers.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 