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
    """You are an expert in web security. Review the HTML structure of a webpage. Differentiate between standard web development practices (like tracking pixels, CAPTCHA forms, hidden fields for state management) and genuinely suspicious characteristics (like obfuscated javascript, forms submitting to external domains, or iframe cloaking). Assess the risk level based on your findings.
    ignore captchas.
    HTML: {html_content}

    Provide your response in the following format:
    - Claim: [Is the HTML structure Benign, Suspicious, or Malicious?]
    - Confidence: [A score between 0 and 1]
    - Evidence: [List the elements and explain why they are either standard practice or genuinely suspicious.]"""
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
    """You are a brand impersonation detection expert. Based on the URL and the HTML-visible content, evaluate whether this page attempts to impersonate a known brand. Focus on brand names, company references, login language, and any indications of misused identity.

    URL: {url}
    Visible Text: {cleaned_text}

    Provide response in the following format:
    - Claim: [Does the content attempt to impersonate a known brand?]
    - Identified Brand: [Provide ONLY the single, clean name of the brand, e.g., 'Amazon', 'Microsoft', 'PayPal'. If none, write 'N/A'.]
    - Confidence: [A score between 0 and 1]
    - Evidence: [Name(s) of impersonated brands and supporting context]"""
)

# Add this to your prompts.py file
visual_anomaly_prompt = PromptTemplate.from_template(
    """You are a visual forensics expert. Your task is to objectively compare two webpage screenshots. Pay close attention to branding, layout, and professionalism.

    Suspicious Screenshot: {suspicious_screenshot}
    Legitimate Screenshot: {legitimate_screenshot}

    Your Task:
    1.  Compare the two screenshots.
    2.  If they are visually similar and both appear professionally designed for the same brand, conclude that the visual risk is Low. Regional differences (like currency or language options) or different sub-pages (like a login page vs. a marketing page) on an official domain are not suspicious.
    3.  If the suspicious screenshot looks amateurish, has low-quality assets, or a different layout, conclude the risk is High.

    Provide a report in the following format:
    - Comparison Verdict: [Are the screenshots visually IDENTICAL, SIMILAR, or DIFFERENT?]
    - Visual Risk Assessment: [Based on the comparison, assess the likelihood of visual deception (Low, Medium, High).]
    - Justification: [Explain your risk assessment based on the visual evidence.]"""
)


# Coordination and Intent Agents (Your prompts are great)

moderator_prompt = PromptTemplate.from_template(
    """You are the Moderator. Your sole purpose is to determine if the specialist agents have reached a consensus. Review their claims from the latest round.
    
    A "Claim" can be 'phishing', 'benign', or 'suspicious'. Treat 'suspicious' and 'phishing' as being on the same side of the argument against 'benign'.

    - If all agents agree (e.g., all claims are 'phishing' or 'suspicious', or all are 'benign'), respond with only the word: CONSENSUS
    - If there is any disagreement, respond with only the word: CONFLICT

    Latest Analyses:
    {latest_analyses}
    """
)

# NEW: Debate prompt for specialists to re-evaluate their findings
debate_specialist_prompt = PromptTemplate.from_template(
    """You are the {agent_persona}. You are participating in a multi-round debate to determine if a website is a phishing attempt.
    
    This is round {round_number} of the debate. Review the full debate history, paying close attention to the arguments made by other specialists in the previous round.
    
    Your Task:
    Re-evaluate your position based on the new evidence and arguments presented. You can choose to change your claim, stick to your original assessment, or introduce new evidence. Your goal is to help the group reach the correct conclusion.
    
    Full Debate History:
    {debate_history}
    
    Original Data You Analyzed:
    URL: {url}
    HTML: {html_content}
    Visible Text: {cleaned_text}
    
    Provide your updated analysis in the same format as before:
    - Claim: [Your phishing/non-phishing assessment]
    - Confidence: [A score between 0 and 1]
    - Evidence: [Explain your reasoning, specifically addressing points from other agents if relevant.]
    """
)

# UPDATE the judge_prompt to handle the full debate history
judge_prompt = PromptTemplate.from_template(
    """You are an expert cybersecurity judge. Review the entire multi-round debate history to make a final, justified decision.
    Do not include any markdown formatting in your response.
    
    Full Debate History:
    {debate_history}
    
    Verification Data (Ground Truth):
    {verification_results}

    Your Task:
    1.  Weigh the Evidence: Give the highest weight to definitive technical evidence from the Verification results and the URL Analyst. If the domain is confirmed as legitimate, the site should be considered benign unless there is overwhelming evidence of a compromise.
    2.  Analyze the Debate Flow: Consider how agents' opinions evolved. Did an agent change its mind based on compelling evidence from another? This could be a strong signal.
    3.  Resolve Conflicts: Acknowledge the final disagreements and explain which side's evidence is more compelling based on the weighting rules.
    4.  Provide a Final Verdict: State clearly whether the site is PHISHING or BENIGN.
    5.  Justify Your Decision: Write a detailed summary explaining how you weighed the evidence and the debate's progression to reach your verdict.

    Final Verdict: [PHISHING or BENIGN]
    Justification: [Your detailed reasoning here.]"""
)

intent_agent_prompt = PromptTemplate.from_template(
    """A webpage has been confirmed as PHISHING. Based on the specialist analyses, identify its malicious intention from: 'Credential Theft', 'Financial Fraud', 'Malware Distribution', 'Personal Information Harvesting'.
    Analyses: {analyses}
    
    Intention:"""
)