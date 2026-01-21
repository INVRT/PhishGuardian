# weighting.py

import math
from phish_guardian_lib.learning.agent_scores import agent_scores

def compute_weight(score: float) -> float:
    """
    Smooth logistic mapping from score → weight in [0, 1].
    score=0 → 0.5
    score>0 → >0.5
    score<0 → <0.5
    """
    return 1 / (1 + math.exp(-score))


def get_agent_weights() -> dict:
    """
    Converts current agent_scores into agent_weights
    using the logistic mapping.
    """
    weights = {}
    for agent, score in agent_scores.items():
        weights[agent] = compute_weight(score)
    return weights


def print_agent_weights():
    """
    Debug helper for visualization during experiments.
    """
    weights = get_agent_weights()
    print("\n=== Current Agent Weights ===")
    for agent, w in weights.items():
        print(f"{agent}: {w:.3f}")
