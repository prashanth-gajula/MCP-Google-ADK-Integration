def strip_html_tags(html_text):
    """Simple HTML tag stripper (use BeautifulSoup for better results)"""
    import re
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', html_text)
    # Decode HTML entities
    import html
    text = html.unescape(text)
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()