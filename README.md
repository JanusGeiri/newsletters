# Automated Newsletter Generation System

This project is an automated system for generating and sending newsletters based on news articles. It includes functionality for scraping news, generating newsletters using AI, formatting them, and sending them to subscribers.

## Features

- News scraping and aggregation from multiple sources
- AI-powered newsletter generation using GPT-4
- Automated newsletter formatting and sending via Gmail API
- Web interface for viewing newsletters
- Unsubscribe management
- Index page generation for newsletter archives
- Automated daily newsletter generation via GitHub Actions

## Prerequisites

- Python 3.8 or higher
- OpenAI API key
- Gmail account with app password for automation
- Google Sheets API access

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

## Project Structure

### Main Scripts
- `src/scripts/main.py`: Main entry point for running the newsletter system
- `src/scripts/automate_newsletter.py`: Automated newsletter generation script (used by GitHub Actions)
- `src/scripts/news_scraper.py`: Scrapes news articles from various sources
- `src/scripts/newsletter_generator.py`: Generates newsletters using AI
- `src/scripts/newsletter_formatter.py`: Formats newsletters for email and web display
- `src/scripts/send_newsletter.py`: Handles newsletter distribution via Gmail API
- `src/scripts/process_unsubscribes.py`: Manages unsubscribe requests
- `src/scripts/update_index.py`: Updates the index.html file with new newsletters
- `src/scripts/serve.py`: Web server for viewing newsletters (development only)
- `src/scripts/newsletter_schemas.py`: Defines newsletter types and schemas
- `src/scripts/logger_config.py`: Configures logging for the application

### Directories
- `src/prompts/`: Contains prompt templates for different newsletter types
- `src/outputs/`: Stores generated newsletters and news articles
- `src/logs/`: Contains log files
- `src/style/`: Contains styling templates for newsletters

## Usage

### Running the Newsletter System

1. To run the complete newsletter generation and sending process:
```bash
python src/scripts/main.py
```

2. To run automated newsletter generation (used by GitHub Actions):
```bash
python src/scripts/automate_newsletter.py
```

### Individual Components

1. Scrape news articles:
```bash
python src/scripts/news_scraper.py
```

2. Generate a newsletter:
```bash
python src/scripts/newsletter_generator.py --type DAILY_MORNING --date YYYY-MM-DD
```

Available newsletter types:
- `DAILY_MORNING` (Currently Active)
- `DAILY_NOON` (In Progress)
- `DAILY_EVENING` (In Progress)
- `WEEKLY` (In Progress)

3. Send a generated newsletter:
```bash
python src/scripts/send_newsletter.py --type DAILY_MORNING --date YYYY-MM-DD
```

4. View newsletters locally:
```bash
python src/scripts/serve.py
```
Then visit `http://localhost:5000` in your browser.

5. Process unsubscribe requests:
```bash
python src/scripts/process_unsubscribes.py
```

## Automation

The system is configured to automatically generate and send newsletters daily using GitHub Actions. The `automate_newsletter.py` script handles this automation process.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 