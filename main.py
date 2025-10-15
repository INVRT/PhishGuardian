# main.py

import json
from phish_guardian_lib.workflow import app as phish_guardian_app
from phish_guardian_lib.utils import preprocess_webpage
from phish_guardian_lib.tools.web_fetcher_tool import fetch_webpage_content
import webbrowser
import pathlib
import tempfile

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

    # Render the report into the HTML template and open it in the default browser
    try:
        template_path = pathlib.Path("templat.html")
        if not template_path.exists():
            print("Template file templat.html not found. Skipping HTML report generation.")
            return

        html = template_path.read_text(encoding="utf-8")

        # Find 'const reportData = ' and replace the JS object following it by matching braces.
        marker = 'const reportData = '
        start = html.find(marker)
        if start == -1:
            print("Marker 'const reportData = ' not found in template. Skipping HTML report generation.")
            return

        obj_start = html.find('{', start)
        if obj_start == -1:
            print("Could not find object start after reportData marker. Skipping.")
            return

        # Find matching closing brace
        depth = 0
        idx = obj_start
        end_idx = -1
        while idx < len(html):
            if html[idx] == '{':
                depth += 1
            elif html[idx] == '}':
                depth -= 1
                if depth == 0:
                    end_idx = idx
                    break
            idx += 1

        if end_idx == -1:
            print("Could not find matching closing brace for reportData object. Skipping.")
            return

        before = html[:start]
        after = html[end_idx+1:]
        injected_obj = json.dumps(report, indent=2)
        new_html = before + marker + injected_obj + after

        tmp = pathlib.Path(tempfile.gettempdir()) / "phishguardian_report.html"
        tmp.write_text(new_html, encoding="utf-8")
        webbrowser.open_new_tab(tmp.as_uri())
        print(f"Opened report in browser: {tmp}")
    except Exception as e:
        print(f"Failed to render/open HTML report: {e}")


if __name__ == "__main__":

    # sample_url = "https://www.amazon.com/" 
    sample_url = "https://official.startamazonstore.com:37831/#/pages/login/login"
    analyze_url(sample_url)