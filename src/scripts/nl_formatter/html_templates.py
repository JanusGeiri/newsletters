"""
HTML templates and formatting utilities for the newsletter.

Note: For best mobile compatibility, use <div class="newsletter-title"> and <div class="newsletter-date"> for the main title and date in the newsletter header.
"""
from typing import Dict, List, Optional
from nl_utils.file_handler import FileHandler, FileType


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

    def __init__(self):
        self.file_handler = FileHandler()

    @staticmethod
    def format_text(text: str) -> str:
        """Convert text with line breaks to HTML."""
        if not text:
            return ""
        return text.replace('\n\n', '<br><br>').replace('\n', '<br>')

    @staticmethod
    def calculate_reading_time(text: str) -> int:
        """Calculate reading time in minutes based on text length.

        Args:
            text (str): The text to calculate reading time for

        Returns:
            int: Estimated reading time in minutes
        """
        if not text:
            return 0
        # Average reading speed: 200 words per minute
        words = len(text.split())
        minutes = max(1, round(words / 240))
        return minutes

    @staticmethod
    def create_footnote_links(urls: List[str], prefix: str = '') -> str:
        """Create footnote links for URLs."""
        if not urls:
            return ""
        links = []
        for i, url in enumerate(urls, 1):
            footnote_id = f"{prefix}fn{i}"
            links.append(
                f'<a href="{url}" class="footnote-link" data-tooltip="{url}" id="{footnote_id}" target="_blank">[{i}]</a>')
        return ' '.join(links)

    @staticmethod
    def create_reading_time_html(minutes: int, is_total: bool = False) -> str:
        """Create HTML for reading time display.

        Args:
            minutes (int): Number of minutes to read
            is_total (bool): Whether this is the total reading time

        Returns:
            str: HTML for reading time display
        """
        label = "Heildar lestur" if is_total else "Lestur"
        return f"""
        <div class="reading-time-container {'total' if is_total else 'section'}">
            <div class="reading-time-icon">⏱️</div>
            <div class="reading-time-content">
                <span class="reading-time-label">{label}:</span>
                <span class="reading-time-value"> {minutes} mín.</span>
            </div>
        </div>
        """

    @staticmethod
    def create_section_html(section_id: str, section_title: str, content: str) -> str:
        """Create HTML for a section."""
        # Calculate reading time for this section
        reading_time = NewsletterTemplate.calculate_reading_time(content)
        reading_time_html = NewsletterTemplate.create_reading_time_html(reading_time)

        return f"""
        <div class="section" id="{section_id}">
            <div class="section-header-container">
                <h2 class="section-header">{section_title}</h2>
                <a href="#toc" class="back-to-toc">← Efnisyfirlit</a>
            </div>
            {reading_time_html}
            <div class="section-content">
                {content}
            </div>
        </div>
        """

    @staticmethod
    def create_news_item_html(
            title: str, description: str, urls: List[str],
            tags: List[str],
            impact: Optional[str] = None, impact_urls: Optional[List[str]] = None, matches: Optional[List[Dict]] = None,
            article_group_names: Optional[Dict[str, str]] = None,
            article_group_urls: Optional[Dict[str, List[str]]] = None) -> str:
        """Create HTML for a news item with title, description, and optional impact."""
        # Format the title and description
        formatted_title = NewsletterTemplate.format_text(title)
        formatted_description = NewsletterTemplate.format_text(description)

        # Create the base HTML structure
        html = f"""
        <div class="news-item">
            <h3>{formatted_title}</h3>
            <p>{formatted_description}</p>
        """

        # Add source links if present
        if urls:
            source_links = NewsletterTemplate.create_footnote_links(urls)
            html += f"""
            <div class="sources">
                <strong>Heimildir:</strong> {source_links}
            </div>
            """

        # Add group URLs if present
        if matches and article_group_urls:
            group_urls = []
            for match in matches:
                group_id = match.get('group_id', '')
                if group_id in article_group_urls:
                    group_urls.extend(article_group_urls[group_id])

            if group_urls:
                # Remove duplicates while preserving order
                unique_urls = list(dict.fromkeys(group_urls))
                group_links = NewsletterTemplate.create_footnote_links(unique_urls, 'group-')
                html += f"""
                <div class="group-sources">
                    <div class="group-sources-header">
                        <strong>Tengdar fréttir</strong>
                        <div class="group-sources-tooltip">
                            <span class="tooltip-icon">ℹ️</span>
                            <div class="tooltip-content">
                                Í einhverjum tilvikum gætu tengdar fréttir vísað á vitlausar slóðir
                                <a href="/why-wrong-links">Af hverju?</a>
                            </div>
                        </div>
                    </div>
                    {group_links}
                </div>
                """

        # Add impact section if present
        if impact:
            formatted_impact = NewsletterTemplate.format_text(impact)
            impact_links = NewsletterTemplate.create_footnote_links(
                impact_urls or [], 'impact-')
            html += f"""
            <div class="impact">
                <strong>Áhrif:</strong> {formatted_impact}
                {impact_links}
            </div>
            """

        # Add tags if present
        if tags:
            formatted_tags = [
                f'<span class="tag">{tag}</span>' for tag in tags]
            html += f"""
            <div class="tags">
                {''.join(formatted_tags)}
            </div>
            """

        # Add matches if present
        if matches:
            # Create the matches content
            matches_html = """
            <div class="matches">
                <p>Við teljum að þessar fréttir passi hér með eftirfarandi líkum:</p>
                <ul>
            """

            for match in matches:
                group_id = match.get('group_id', '')
                group_name = article_group_names.get(group_id, '')
                probability = match.get('probability', 0)
                probability_pct = f"{probability * 100:.2f}%"
                matches_html += f"""
                    <li>
                        <span>{group_name}</span>
                        <span>{probability_pct}</span>
                    </li>
                """

            matches_html += """
                </ul>
                <p><a href="/how-matches-work">Hvað er þetta?</a></p>
            </div>
            """

            html += f"""
            <div class="matches-container">
                <div class="match">
                    <span class="match-icon">✨</span>
                    <div class="match-tooltip">
                        {matches_html}
                    </div>
                </div>
            </div>
            """

        html += "</div>"
        return html

    @staticmethod
    def create_summary_html(
            main_headline: str, summary: str, summary_impact: Optional[str] = None,
            summary_impact_urls: Optional[List[str]] = None) -> str:
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

        # Calculate reading time for summary
        reading_time = NewsletterTemplate.calculate_reading_time(summary + (summary_impact or ''))
        reading_time_html = NewsletterTemplate.create_reading_time_html(reading_time)

        return f"""
        <div class="section" id="summary">
            <div class="section-header-container">
                <h2 class="section-header">{main_headline}</h2>
            </div>
            {reading_time_html}
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

    def get_css_styles(self) -> str:
        """Get CSS styles for the newsletter."""
        return self.file_handler.load_file(
            FileType.TEXT,
            base_name='nl_style'
        )
