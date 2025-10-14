from langchain.tools import tool
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import os
from urllib.parse import urlparse, quote
import re

@tool
def fetch_webpage_content(url: str) -> dict:
    """
    Navigates to a URL to fetch its HTML content and take a screenshot.
    Returns a dictionary with the HTML and the path to the screenshot.
    """
    print(f"--- TOOL USED: Fetching content for '{url}' ---")
    
    # Define the correct path inside the library
    screenshot_dir = "phish_guardian_lib/screenshots"
    os.makedirs(screenshot_dir, exist_ok=True)

    # If the URL is a blob: URL, it cannot be fetched directly from outside the page
    # Blob URLs are in-memory object URLs created by a page's JS context. Mark them as suspicious.
    if url.strip().lower().startswith("blob:"):
        return {
            "error": f"Blob URLs cannot be fetched externally: {url}",
            "screenshot_path": None,
            "html_content": None,
            "decision": "PHISHING",
            "reason": "PHISHING - Blob URL detected — not fetchable outside original page context"
        }
    
    # Sanitize URL to create a safe filename for Windows and other OSes.
    # Parse the URL and build a filename from netloc + path, percent-encoding unsafe parts.
    parsed = urlparse(url.strip())
    # If urlparse failed to identify netloc (e.g., url has leading whitespace or tabs), fallback
    netloc = (parsed.netloc or parsed.path).strip()
    path = parsed.path or ""

    # Combine netloc and path and percent-encode
    combined = netloc + path
    # Replace backslashes, tabs, and control characters
    combined = re.sub(r"[\x00-\x1f\\<>:\"/|?*]", "_", combined)
    # Truncate to reasonable length
    if len(combined) > 200:
        combined = combined[:200]

    safe_filename = f"{combined}_suspicious.png"
    screenshot_path = os.path.join(screenshot_dir, safe_filename)
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            page.goto(url, timeout=15000)
            
            # Fetch HTML content
            html_content = page.content()
            
            # Take screenshot
            page.screenshot(path=screenshot_path, full_page=True)
            
            browser.close()
            
            return {
                "html_content": html_content,
                "screenshot_path": screenshot_path
            }
    except Exception as e:
        return {"error": f"Failed to fetch content from {url}. Reason: {e}"}