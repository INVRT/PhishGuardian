# score_update.py

from phish_guardian_lib.learning.agent_scores import agent_scores


def extract_claim(text: str) -> str:
    """
    Attempts to extract the claim label from a specialist response.
    Normalizes variations like 'Suspicious' → 'PHISHING'
    """
    text = text.lower()

    if "phishing" in text or "suspicious" in text or "malicious" in text:
        return "PHISHING"
    if "benign" in text or "legitimate" in text:
        return "BENIGN"
    return "UNKNOWN"


def update_agent_scores(final_state, verdict: str):
    """
    Updates each agent's score based on defender outcome.
    verdict: PHISHING or BENIGN (from Judge)
    """

    # Get last debate round analyses
    last_round = final_state['debate_history'][-1]['analyses']

    for agent, report in last_round.items():
        claim = extract_claim(report)

        # Case A: Defender succeeded (detected phishing)
        if verdict == "PHISHING":
            if claim == "PHISHING":
                agent_scores[agent] += 1
            elif claim == "BENIGN":
                agent_scores[agent] -= 1

        # Case B: Defender failed (bypass)
        elif verdict == "BENIGN":
            if claim == "BENIGN":
                agent_scores[agent] -= 2
            elif claim == "PHISHING":
                agent_scores[agent] += 0

    return agent_scores
