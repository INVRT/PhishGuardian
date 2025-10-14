# in online_search.py

import os
import requests
from urllib.parse import urlparse
from langchain.tools import tool

@tool
def search_online_knowledge(query: str, search_type: str, content_keywords: str = "") -> list:
    """
    Searches the web using the Google Custom Search JSON API to verify a domain or find official brand websites.
    'search_type' must be 'domain' or 'brand'.
    'content_keywords' is an optional string of keywords from the webpage to refine brand searches.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    cse_id = os.getenv("GOOGLE_CSE_ID")
    
    if not api_key or not cse_id:
        print("Error: Google API Key or CSE ID is not configured.")
        return []

    # The search query is formatted differently based on the search type
    if search_type == "domain":
        search_query = f"site:{query}"
    elif search_type == "brand":
        # ENHANCED: Append content keywords if they exist to create a smarter query
        search_query = f"{query} official website"
        if content_keywords:
            search_query += f" {content_keywords}"
    else:
        return []

    # This print statement will now show the enhanced query
    print(f"--- TOOL USED: Searching for '{search_query}' (type: {search_type}) ---")

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'key': api_key,
        'cx': cse_id,
        'q': search_query,
        'num': 5
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        results = response.json()

        if not results.get("items"):
            return []

        found_domains = set()
        for item in results["items"]:
            link = item.get("link")
            if link:
                domain = urlparse(link).netloc
                if domain.startswith('www.'):
                    domain = domain[4:]
                found_domains.add(domain)
        
        return list(found_domains)

    except requests.exceptions.RequestException as e:
        print(f"Error making search API request: {e}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return []