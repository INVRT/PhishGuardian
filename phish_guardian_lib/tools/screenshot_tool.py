import os
from langchain.tools import tool
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

@tool
def take_screenshot_of_url(url: str) -> str:
    """
    Takes a screenshot of a given URL and saves it to a file.
    Returns the file path of the saved screenshot or an error message.
    """
    print(f"--- TOOL USED: Taking screenshot of '{url}' ---")
    
    # Define the correct path inside the library
    screenshot_dir = "phish_guardian_lib/screenshots"
    os.makedirs(screenshot_dir, exist_ok=True)
    
    # Sanitize the URL to create a valid filename
    safe_filename = url.replace('http://', '').replace('https://', '').replace('/', '_') + ".png"
    file_path = os.path.join(screenshot_dir, safe_filename)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            # Set a timeout for navigation
            page.goto(url, timeout=15000) 
            page.screenshot(path=file_path, full_page=True)
            browser.close()
            return file_path
    except PlaywrightTimeoutError:
        return f"Error: Navigation timed out for URL: {url}"
    except Exception as e:
        return f"Error: Could not take screenshot of {url}. Reason: {e}"