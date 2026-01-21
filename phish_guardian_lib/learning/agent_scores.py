# agent_scores.py

"""
Stores performance scores for agents in AEGIS that update based on defender success/failure.
Higher score → higher influence in judge evaluation.
"""

agent_scores = {
    "URL Analyst": 0.0,
    "HTML Analyst": 0.0,
    "Content Analyst": 0.0,
    "Brand Analyst": 0.0,
    "Visual Analyst": 0.0,
}

def get_scores():
    return agent_scores

def reset_scores():
    for k in agent_scores.keys():
        agent_scores[k] = 0.0
