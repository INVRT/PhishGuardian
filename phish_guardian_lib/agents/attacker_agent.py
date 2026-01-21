from phish_guardian_lib.config import llm

def generate_phishing_variant(target_brand: str):
    prompt = f"""
You are an adversarial phishing designer.
Generate a phishing login page that avoids explicit phishing cues and aims to bypass automated phishing detection systems.

Target brand: {target_brand}

Avoid explicit phishing keywords such as:
login, verify, password, urgent, suspended, credential, phishing, scam.

Use a subtle transactional tone.

Output in JSON format:
{{
  "fake_url": "...",
  "page_text": "...",
  "html_snippet": "...",
  "evasion_strategy": "..."
}}
"""
    result = llm.invoke(prompt)
    return result.content
