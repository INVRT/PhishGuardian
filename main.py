# main.py

import json
from phish_guardian_lib.workflow import app as phish_guardian_app
from phish_guardian_lib.utils import preprocess_webpage
from phish_guardian_lib.tools.web_fetcher_tool import fetch_webpage_content

def analyze_url(url: str):
    """
    Runs the full PhishGuardian analysis with debate starting from just a URL.
    """
    print(f"--- Starting PhishGuardian Analysis for: {url} ---")
    
    web_data = fetch_webpage_content.invoke(url)
    if "error" in web_data:
        print(web_data["error"])
        return

    html_content = web_data["html_content"]
    screenshot_path = web_data["screenshot_path"]
    
    preprocessed_data = preprocess_webpage(url, html_content)
    
    # Initialize the state for the graph
    initial_state = {
        "webpage_data": preprocessed_data,
        "screenshot": screenshot_path,
        "debate_history": [],
        "round_number": 0,
    }
    
    # Invoke the graph
    final_state = phish_guardian_app.invoke(initial_state)

    # Compile the final report
    report = {
        "decision": final_state.get('judge_verdict'),
        "reasoning": final_state.get('judge_reasoning'),
        "malicious_intention": final_state.get('malicious_intention', 'N/A'),
        "debate_summary": final_state.get('debate_history', []),
        "verification_data": final_state.get('verification_results')
    }
    
    print("\n--- PhishGuardian Final Report ---")
    print(json.dumps(report, indent=2))
    print("---------------------------------")


if __name__ == "__main__":
    # Example that might cause conflict (e.g., a simple login page on a weird domain)
    # Replace with a URL you want to test
    sample_url = "https://www.amazon.in/" 
    analyze_url(sample_url)