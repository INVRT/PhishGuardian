import os
import requests
from urllib.parse import urlparse
from langchain.tools import tool

@tool
def search_online_knowledge(query: str, search_type: str) -> list:
    """
    Searches the web using the Google Custom Search JSON API to verify a domain or find official brand websites.
    'search_type' must be 'domain' or 'brand'.
    """
    print(f"--- TOOL USED: Searching for '{query}' (type: {search_type}) ---")

    api_key = os.getenv("GOOGLE_API_KEY")
    cse_id = os.getenv("GOOGLE_CSE_ID")
    
    if not api_key or not cse_id:
        print("Error: Google API Key or CSE ID is not configured.")
        return []

    # The search query is formatted differently based on the search type
    if search_type == "domain":
        # Using "site:" operator is a good way to check if a domain is well-known
        search_query = f"site:{query}"
    elif search_type == "brand":
        search_query = f"{query} official website"
    else:
        return []

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'key': api_key,
        'cx': cse_id,
        'q': search_query,
        'num': 5 # We only need the top few results
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes
        results = response.json()

        if not results.get("items"):
            return []

        # Extract the root domain (netloc) from each search result link
        found_domains = set()
        for item in results["items"]:
            link = item.get("link")
            if link:
                domain = urlparse(link).netloc
                # Standardize by removing 'www.' if it exists
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