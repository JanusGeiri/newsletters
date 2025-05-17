"""
HTML templates and formatting utilities for the newsletter.
"""
from typing import Dict, List, Optional


class NewsletterTemplate:
    """Template configuration for newsletter formatting."""

    # Text configuration
    TEXT_CONFIG = {
        'title': 'Fréttir Gærdagsins',
        'signature': 'Fréttabréfið er skrifað af gervigreind frá OpenAI. Gæti innihaldið ofsjónir. Verkefni forritað af Jasoni Andra Gíslasyni.',
        'unsubscribe_text': 'Hætta áskrift á fréttabréfinu',
        'unsubscribe_link': 'https://docs.google.com/forms/d/e/1FAIpQLSfHWhr9DmTtrtazcCANt-yjpxoAmF9ZEj_lQKZmCwQAqQNZzw/viewform?usp=header',
        'sections': {
            'key_events': '1. MIKILVÆGUSTU FRÉTTIRNAR',
            'domestic_news': '2. INNLENT',
            'foreign_news': '3. ERLENT',
            'business': '4. VIÐSKIPTI',
            'famous_people': '5. FRÆGA FÓLKIÐ',
            'sports': '6. ÍÞRÓTTIR',
            'arts': '7. LISTIR',
            'science': '8. VÍSINDI',
            'closing_summary': '9. LOKAORÐ'
        }
    }

    @staticmethod
    def format_text(text: str) -> str:
        """Convert text with line breaks to HTML."""
        if not text:
            return ""
        return text.replace('\n\n', '<br><br>').replace('\n', '<br>')

    @staticmethod
    def create_footnote_links(urls: List[str], prefix: str = '') -> str:
        """Create footnote links for URLs."""
        if not urls:
            return ""
        links = []
        for i, url in enumerate(urls, 1):
            footnote_id = f"{prefix}fn{i}"
            links.append(
                f'<a href="{url}" class="footnote-link" data-tooltip="{url}" id="{footnote_id}">[{i}]</a>')
        return ' '.join(links)

    @staticmethod
    def create_section_html(section_id: str, section_title: str, content: str) -> str:
        """Create HTML for a section."""
        return f"""
        <div class="section" id="{section_id}">
            <div class="section-header-container">
                <h2 class="section-header">{section_title}</h2>
                <a href="#toc" class="back-to-toc">← Efnisyfirlit</a>
            </div>
            <div class="section-content">
                {content}
            </div>
        </div>
        """

    @staticmethod
    def create_news_item_html(title: str, description: str, urls: List[str], tags: List[str], impact: Optional[str] = None, impact_urls: Optional[List[str]] = None, match: Optional[Dict] = None) -> str:
        """Create HTML for a news item.

        Args:
            title (str): The news item title
            description (str): The news item description
            urls (List[str]): List of article URLs
            tags (List[str]): List of tags
            impact (Optional[str]): Impact description
            impact_urls (Optional[List[str]]): List of impact-related URLs
            match (Optional[Dict]): Match information containing group_id and similarity

        Returns:
            str: HTML for the news item
        """
        # Create footnote links for article URLs
        item_urls = NewsletterTemplate.create_footnote_links(urls)

        # Add impact section if available
        impact_html = ""
        if impact:
            impact_urls_html = NewsletterTemplate.create_footnote_links(
                impact_urls or [], 'impact')
            impact_html = f'<div class="impact-section"><strong>Áhrif:</strong> {NewsletterTemplate.format_text(impact)} {impact_urls_html}</div>'

        # Add match information if available
        match_html = ""
        if match and match.get('group_id'):
            similarity = match.get('similarity', 0.0)
            match_html = f'<div class="match-info" data-tooltip="Match: {match["group_id"]} (similarity: {similarity:.2f})">⚡</div>'

        return f"""
        <div class="news-item">
            <h3>{title}</h3>
            <p>{NewsletterTemplate.format_text(description)} {item_urls}</p>
            {impact_html}
            {match_html}
            <div class="tags">
                {' '.join(f'<span class="tag">{tag}</span>' for tag in tags)}
            </div>
        </div>
        """

    @staticmethod
    def create_summary_html(main_headline: str, summary: str, summary_impact: Optional[str] = None, summary_impact_urls: Optional[List[str]] = None) -> str:
        """Create HTML for the summary section.

        Args:
            main_headline (str): The main headline
            summary (str): The summary text
            summary_impact (Optional[str]): Impact description for the summary
            summary_impact_urls (Optional[List[str]]): List of impact-related URLs for the summary

        Returns:
            str: HTML for the summary section
        """
        impact_html = ""
        if summary_impact:
            impact_urls_html = NewsletterTemplate.create_footnote_links(
                summary_impact_urls or [], 'summary-impact')
            impact_html = f'<div class="impact-section"><strong>Áhrif:</strong> {NewsletterTemplate.format_text(summary_impact)} {impact_urls_html}</div>'

        return f"""
        <div class="section" id="summary">
            <div class="section-header-container">
                <h2 class="main-headline">{main_headline}</h2>
                <a href="#toc" class="back-to-toc">← Efnisyfirlit</a>
            </div>
            <div class="section-content">
                <p>{NewsletterTemplate.format_text(summary)}</p>
                {impact_html}
            </div>
        </div>
        """

    @staticmethod
    def create_toc_html(sections: Dict[str, str]) -> str:
        """Create table of contents HTML."""
        toc_items = []
        for section_id, section_title in sections.items():
            toc_items.append(
                f'<a href="#{section_id}" class="toc-item">{section_title}</a>')

        return f"""
        <div class="section toc-section" id="toc">
            <h2 class="section-header">Efnisyfirlit</h2>
            <div class="toc-container">
                {''.join(toc_items)}
            </div>
        </div>
        """

    @staticmethod
    def get_css_styles() -> str:
        """Get CSS styles for the newsletter."""
        return """
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            color: #2c3e50;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }
        .section {
            background-color: #ffffff;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.2s ease;
        }
        .section:hover {
            transform: translateY(-2px);
        }
        .section-header-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        .back-to-toc {
            color: #666;
            text-decoration: none;
            font-size: 0.9em;
            padding: 5px 10px;
            border-radius: 15px;
            background-color: #f8f9fa;
            transition: all 0.2s ease;
        }
        .back-to-toc:hover {
            background-color: #3498db;
            color: white;
        }
        .title-section {
            text-align: center;
            background: linear-gradient(135deg, #2c3e50, #3498db);
            color: white;
            padding: 40px 20px;
            border-radius: 12px;
        }
        .newsletter-title {
            font-size: 2.4em;
            margin: 0;
            font-weight: bold;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        .newsletter-date {
            font-size: 1.2em;
            margin: 10px 0 0;
            opacity: 0.9;
        }
        .main-headline {
            color: #2c3e50;
            font-size: 1.8em;
            margin: 0;
            padding-bottom: 15px;
            border-bottom: 3px solid #3498db;
        }
        .section-header {
            color: #2c3e50;
            font-size: 1.5em;
            margin: 0;
            padding-bottom: 10px;
            border-bottom: 2px solid #e9ecef;
        }
        .section-content {
            color: #444;
        }
        .news-item {
            margin-bottom: 25px;
            padding-bottom: 20px;
            border-bottom: 1px solid #e9ecef;
            position: relative;
        }
        .news-item:last-child {
            border-bottom: none;
        }
        .news-item h3 {
            color: #2c3e50;
            margin-top: 0;
            margin-bottom: 12px;
            font-size: 1.3em;
        }
        .impact-section {
            font-style: italic;
            color: #666;
            margin: 12px 0;
            padding: 10px;
            background-color: #f8f9fa;
            border-left: 4px solid #3498db;
        }
        .match-info {
            position: absolute;
            top: 10px;
            right: 10px;
            font-size: 1.2em;
            cursor: help;
        }
        .match-info[data-tooltip]:hover::after {
            content: attr(data-tooltip);
            position: absolute;
            top: 100%;
            right: 0;
            padding: 8px;
            background-color: #2c3e50;
            color: white;
            border-radius: 4px;
            font-size: 0.9em;
            white-space: nowrap;
            z-index: 1000;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        .tags {
            margin-top: 12px;
        }
        .tag {
            display: inline-block;
            background-color: #e9ecef;
            color: #495057;
            padding: 4px 10px;
            border-radius: 20px;
            margin-right: 8px;
            font-size: 0.9em;
            transition: background-color 0.2s ease;
        }
        .tag:hover {
            background-color: #3498db;
            color: white;
        }
        .signature-section {
            text-align: center;
            font-style: italic;
            color: #666;
            border-top: 2px solid #e9ecef;
            margin-top: 40px;
            padding-top: 20px;
        }
        .signature {
            margin: 0;
            font-size: 0.9em;
        }
        .unsubscribe {
            margin-top: 15px;
            font-size: 0.9em;
        }
        .unsubscribe a {
            color: #666;
            text-decoration: none;
            border-bottom: 1px solid #666;
            transition: color 0.2s ease;
        }
        .unsubscribe a:hover {
            color: #3498db;
            border-bottom-color: #3498db;
        }
        .footnote-link {
            color: #3498db;
            text-decoration: none;
            font-size: 0.8em;
            vertical-align: super;
            position: relative;
        }
        .footnote-link:hover {
            color: #2980b9;
        }
        .footnote-link[data-tooltip]:hover::after {
            content: attr(data-tooltip);
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            padding: 8px;
            background-color: #2c3e50;
            color: white;
            border-radius: 4px;
            font-size: 0.9em;
            white-space: nowrap;
            z-index: 1000;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        .toc-section {
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
        }
        .toc-container {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            padding: 10px;
        }
        .toc-item {
            display: inline-block;
            padding: 8px 15px;
            background-color: #e9ecef;
            color: #2c3e50;
            text-decoration: none;
            border-radius: 20px;
            font-size: 0.9em;
            transition: all 0.2s ease;
        }
        .toc-item:hover {
            background-color: #3498db;
            color: white;
            transform: translateY(-2px);
        }
        @media only screen and (max-width: 600px) {
            body {
                padding: 10px;
            }
            .section {
                padding: 15px;
            }
            .newsletter-title {
                font-size: 1.8em;
            }
            .main-headline {
                font-size: 1.5em;
            }
            .section-header {
                font-size: 1.3em;
            }
            .footnote-link[data-tooltip]:hover::after {
                display: none;
            }
            .toc-container {
                flex-direction: column;
            }
            .toc-item {
                width: 100%;
                text-align: center;
            }
            .back-to-toc {
                display: none;
            }
        }
        """
