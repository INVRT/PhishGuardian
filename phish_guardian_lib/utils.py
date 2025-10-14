from bs4 import BeautifulSoup
from urllib.parse import urlparse

def preprocess_webpage(url: str, html_content: str):
    """
    Parses the domain from a URL and cleans HTML content, returning a dictionary
    with the URL, domain, cleaned HTML, and visible text.
    """
    try:
        domain = urlparse(url).netloc
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove non-visible or noisy tags for cleaner analysis
        for element in soup(["script", "style", "head", "meta", "link"]):
            element.decompose()
        
        # Extract visible text and truncate
        cleaned_text = ' '.join(soup.stripped_strings)[:8000]
        
        # Get the cleaned HTML structure and truncate
        truncated_html = str(soup)[:8000]

        return {
            "url": url,
            "domain": domain,
            "cleaned_text": cleaned_text,
            "html_content": truncated_html # Added for the HTML Structure Agent
        }
    except Exception as e:
        print(f"Error during preprocessing: {e}")
        return {} # Return an empty dict on failure