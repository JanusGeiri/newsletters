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

        return f"""
        <div class="section" id="summary">
            <div class="section-header-container">
                <h2 class="main-headline">{main_headline}</h2>
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
        <style>
            /* Base styles */
            body {
                font-family: 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 0;
                color: #2c3e50;
                background-color: #f8f9fa;
            }
            
            .newsletter {
                max-width: 800px;
                margin: 20px auto;
                background-color: #ffffff;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
                border-radius: 12px;
                overflow: hidden;
            }
            
            /* Title section */
            .title-section {
                background: linear-gradient(135deg, #2c3e50, #3498db);
                color: white;
                padding: 40px 20px;
                text-align: center;
                margin-bottom: 0;
            }
            
            .newsletter-title {
                font-size: 2.5em;
                margin: 0;
                font-weight: 300;
                letter-spacing: 1px;
            }
            
            .newsletter-date {
                font-size: 1.2em;
                margin: 10px 0 0;
                opacity: 0.9;
                font-weight: 300;
            }
            
            /* Section styles */
            .section {
                margin: 20px;
                padding: 30px;
                background-color: #ffffff;
                border-radius: 12px;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
            }
            
            .section-content {
                text-align: justify;
            }
            
            .section-header-container {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
            }
            
            .section-header {
                color: #2c3e50;
                font-size: 1.5em;
                margin: 0;
                font-weight: 500;
            }
            
            .back-to-toc {
                font-size: 0.9em;
                color: #666;
                text-decoration: none;
                padding: 5px 10px;
                border-radius: 4px;
                background-color: #f8f9fa;
                transition: all 0.2s ease;
            }
            
            .back-to-toc:hover {
                background-color: #e9ecef;
                color: #2c3e50;
            }
            
            /* News item styles */
            .news-item {
                margin-bottom: 25px;
                padding: 20px;
                background-color: #fafafa;
                border-radius: 8px;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
                position: relative;
            }
            
            .news-item:last-child {
                margin-bottom: 0;
            }
            
            .news-item h3 {
                margin: 0 0 15px;
                color: #2c3e50;
                font-size: 1.3em;
                font-weight: 500;
                line-height: 1.4;
            }
            
            .news-item p {
                margin: 0 0 15px;
                color: #4a5568;
                line-height: 1.6;
                text-align: justify;
            }
            
            /* Impact section */
            .impact {
                margin-top: 15px;
                padding: 12px 15px;
                background-color: #f8f9fa;
                border-left: 3px solid #3498db;
                font-size: 0.95em;
                color: #4a5568;
                text-align: justify;
            }
            
            .impact strong {
                color: #2c3e50;
            }
            
            /* Sources section */
            .sources {
                margin-top: 12px;
                font-size: 0.9em;
                color: #718096;
            }
            
            .sources strong {
                color: #4a5568;
            }

            /* Group sources section */
            .group-sources {
                margin-top: 12px;
                font-size: 0.9em;
                color: #718096;
                border-left: 3px solid #48bb78;
                padding-left: 12px;
            }
            
            .group-sources strong {
                color: #4a5568;
            }

            .group-sources-header {
                display: flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 4px;
            }

            .group-sources-tooltip {
                position: relative;
                display: inline-block;
            }

            .tooltip-icon {
                font-size: 0.9em;
                cursor: help;
                opacity: 0.7;
                transition: opacity 0.2s ease;
            }

            .tooltip-icon:hover {
                opacity: 1;
            }

            .tooltip-content {
                display: none;
                position: absolute;
                left: 50%;
                transform: translateX(-50%);
                bottom: 100%;
                background-color: #2d3748;
                color: white;
                padding: 8px 12px;
                border-radius: 6px;
                font-size: 0.85em;
                width: max-content;
                max-width: 300px;
                margin-bottom: 8px;
                z-index: 1000;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                text-align: justify;
            }

            .tooltip-content::after {
                content: '';
                position: absolute;
                top: 100%;
                left: 50%;
                transform: translateX(-50%);
                border-width: 6px;
                border-style: solid;
                border-color: #2d3748 transparent transparent transparent;
            }

            .group-sources-tooltip:hover .tooltip-content {
                display: block;
            }

            .tooltip-content a {
                color: #63b3ed;
                text-decoration: none;
                margin-left: 4px;
            }

            .tooltip-content a:hover {
                text-decoration: underline;
            }
            
            /* Tags section */
            .tags {
                margin-top: 12px;
            }
            
            .tag {
                display: inline-block;
                padding: 3px 8px;
                margin: 2px;
                background-color: #edf2f7;
                border-radius: 4px;
                font-size: 0.8em;
                color: #4a5568;
            }
            
            /* Matches section */
            .matches-container {
                position: absolute;
                bottom: 10px;
                right: 10px;
                font-size: 0.85em;
                color: #718096;
            }
            
            .match {
                display: inline-block;
                cursor: help;
                position: relative;
                opacity: 0.7;
                transition: opacity 0.2s ease;
            }
            
            .match:hover {
                opacity: 1;
            }
            
            .match-icon {
                font-size: 1.2em;
            }
            
            .match-tooltip {
                display: none;
                position: absolute;
                bottom: 100%;
                right: 0;
                background-color: #ffffff;
                color: #2c3e50;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                z-index: 1000;
                min-width: 300px;
                max-width: 400px;
                margin-bottom: 10px;
            }
            
            .match:hover .match-tooltip {
                display: block;
            }
            
            .matches {
                padding: 15px;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }
            
            .matches p {
                margin: 0 0 10px 0;
                font-weight: 500;
                color: #2c3e50;
                font-size: 0.95em;
                text-align: justify;
            }
            
            .matches ul {
                padding: 0;
                margin: 0 0 10px 0;
                list-style: none;
            }
            
            .matches ul li {
                display: grid;
                grid-template-columns: 1fr auto;
                gap: 15px;
                padding: 8px 0;
                border-bottom: 1px solid #edf2f7;
                font-size: 0.9em;
            }
            
            .matches ul li:last-child {
                border-bottom: none;
            }
            
            .matches ul li span:first-child {
                color: #4a5568;
            }
            
            .matches ul li span:last-child {
                color: #2d3748;
                font-weight: 500;
                text-align: right;
                min-width: 60px;
            }
            
            .matches a {
                color: #3498db;
                text-decoration: none;
                font-size: 0.85em;
            }
            
            .matches a:hover {
                text-decoration: underline;
            }
            
            /* Links */
            a {
                color: #3498db;
                text-decoration: none;
                transition: color 0.2s ease;
            }
            
            a:hover {
                color: #2980b9;
            }
            
            /* Table of contents */
            .toc-section {
                background-color: #f8f9fa;
                padding: 20px 30px;
                margin: 20px;
                border-radius: 12px;
            }
            
            .toc-container {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
            }
            
            .toc-item {
                padding: 6px 12px;
                background-color: #ffffff;
                border-radius: 4px;
                color: #4a5568;
                text-decoration: none;
                font-size: 0.9em;
                transition: all 0.2s ease;
                border: 1px solid #e2e8f0;
            }
            
            .toc-item:hover {
                background-color: #edf2f7;
                color: #2c3e50;
            }
            
            /* Signature section */
            .signature-section {
                margin: 20px;
                padding: 20px 30px;
                background-color: #f8f9fa;
                font-size: 0.85em;
                color: #718096;
                text-align: center;
                border-radius: 12px;
            }
            
            .signature {
                margin: 0 0 10px;
            }
            
            .unsubscribe {
                margin: 0;
            }
            
            .unsubscribe a {
                color: #718096;
                text-decoration: underline;
            }
            
            .unsubscribe a:hover {
                color: #4a5568;
            }

            /* Mobile Responsive Styles */
            @media screen and (max-width: 768px) {
                .newsletter {
                    margin: 0;
                    border-radius: 0;
                    box-shadow: none;
                }

                .section {
                    margin: 3px 0;
                    padding: 4.5px;
                    border-radius: 0;
                }

                .title-section {
                    padding: 9px 4.5px;
                }

                .newsletter-title {
                    font-size: 2em;
                }

                .newsletter-date {
                    font-size: 1em;
                }

                .section-header {
                    font-size: 1.3em;
                }

                .news-item {
                    padding: 4.5px;
                    margin-bottom: 4.5px;
                }

                .news-item h3 {
                    font-size: 1.2em;
                }

                .news-item p {
                    font-size: 0.95em;
                }

                .impact {
                    font-size: 0.9em;
                    padding: 3px;
                }

                .sources, .group-sources {
                    font-size: 0.85em;
                }

                .toc-section {
                    margin: 3px 0;
                    padding: 4.5px;
                }

                .toc-item {
                    font-size: 0.85em;
                    padding: 1.5px 3px;
                }

                .signature-section {
                    margin: 3px 0;
                    padding: 4.5px;
                }

                .signature, .unsubscribe {
                    font-size: 0.8em;
                }

                .match-tooltip {
                    min-width: 250px;
                    max-width: 300px;
                }

                .matches {
                    padding: 3px;
                }

                .matches ul li {
                    font-size: 0.85em;
                    gap: 3px;
                }
            }

            /* Small Mobile Devices */
            @media screen and (max-width: 480px) {
                .newsletter-title {
                    font-size: 1.8em;
                }

                .newsletter-date {
                    font-size: 0.9em;
                }

                .section-header {
                    font-size: 1.2em;
                }

                .news-item h3 {
                    font-size: 1.1em;
                }

                .news-item p {
                    font-size: 0.9em;
                }

                .toc-container {
                    gap: 1.5px;
                }

                .toc-item {
                    font-size: 0.8em;
                    padding: 1.2px 2.4px;
                }
            }
        </style>
        """
