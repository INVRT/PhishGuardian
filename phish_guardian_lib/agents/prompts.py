from langchain_core.prompts import PromptTemplate

# Specialist Agent Prompts (Filled in from phishdebate.pdf)

url_analyst_prompt = PromptTemplate.from_template(
    """You are a cybersecurity expert specializing in URL analysis for phishing detection. Examine the provided URL and identify suspicious patterns, domain characteristics, subdomain usage, URL structure, and any indicators that suggest phishing or legitimate intent.    
    
    URL: {url} 
    
    Provide your response in the following format: 
    - Claim: [Your phishing/non-phishing assessment of the URL] 
    - Confidence: [A score between 0 and 1] 
    - Evidence: [Key suspicious or benign patterns you found] """
)

html_analyst_prompt = PromptTemplate.from_template(
    """You are an expert in web security. Review the HTML structure of a webpage and determine if it exhibits suspicious structural characteristics typical of phishing sites. [cite: 389] Focus on elements such as hidden forms, suspicious input fields, iframe usage, obfuscated JavaScript, and deceptive redirection patterns.
    
    HTML: {html_content} 
    
    Provide your response in the following format: 
    - Claim: [Your assessment about the HTML structure indicating phishing or not] 
    - Confidence: [A score between 0 and 1] 
    - Evidence: [Relevant structural elements or tag patterns you found]"""
)

content_analyst_prompt = PromptTemplate.from_template(
    """You are a cybersecurity-focused language expert. Read the visible text content extracted from a webpage and decide whether the language indicates phishing intent. [cite: 399] Look for emotionally manipulative language, requests for sensitive information, login instructions, urgency, or impersonation of known organizations. 
    
    Visible Text: {cleaned_text} 
    
    Provide your response in the following format: 
    - Claim: [Whether the page language seems phishing-related] 
    - Confidence: [A score between 0 and 1]
    - Evidence: [Specific words, phrases, or sentence patterns that support your claim]"""
)

brand_analyst_prompt = PromptTemplate.from_template(
    """You are a brand impersonation detection expert. Based on the URL and the HTML-visible content, evaluate whether this page attempts to impersonate a known brand. [cite: 409] Focus on brand names, company references, login language, and any indications of misused identity (such as pretending to be Google, Apple, PayPal, etc.). 
    
    URL: {url} 
    Visible Text: {cleaned_text} 
    
    Provide response in following format: 
    - Claim: [Does the content attempt to impersonate a known brand?] 
    - Confidence: [A score between 0 and 1] 
    - Evidence: [Name(s) of impersonated brands and supporting context]"""
)

# Add this to your prompts.py file
visual_anomaly_prompt = PromptTemplate.from_template(
    """You are a visual deception expert specializing in phishing detection. Your task is to analyze a suspicious webpage screenshot and compare it with a screenshot of its legitimate counterpart.

    1.  **Analyze the Suspicious Screenshot for Anomalies**: Look for low-resolution logos, awkward layouts, pixelation, unusual fonts, or any other visual elements that appear unprofessional or out of place.
    2.  **Compare with Legitimate Screenshot**: Identify key differences in branding, layout, color scheme, and component placement between the suspicious and legitimate screenshots.

    **Suspicious Screenshot**: {suspicious_screenshot}
    **Legitimate Screenshot**: {legitimate_screenshot}

    Provide a report in the following format:
    - **Anomaly Assessment**: [Describe any visual anomalies found in the suspicious screenshot.]
    - **Comparison Verdict**: [Are the screenshots visually similar or different?]
    - **Key Differences**: [List the specific visual differences you observed.]"""
)


# Coordination and Intent Agents (Your prompts are great)

judge_prompt = PromptTemplate.from_template(
    """You are an expert cybersecurity judge. Review the entire debate history, including specialist analyses and real-world verification results, to make a final decision.
    History: {history}
    
    Final Verdict (PHISHING or BENIGN):"""
)

intent_agent_prompt = PromptTemplate.from_template(
    """A webpage has been confirmed as PHISHING. Based on the specialist analyses, identify its malicious intention from: 'Credential Theft', 'Financial Fraud', 'Malware Distribution', 'Personal Information Harvesting'.
    Analyses: {analyses}
    
    Intention:"""
)