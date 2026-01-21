# simulator.py

import json
from phish_guardian_lib.workflow import app as phish_guardian_app
from phish_guardian_lib.attacker import generate_phishing_variant


def defend(attack_data: dict):
    """
    Feeds attacker-generated phishing into the AEGIS defender pipeline
    without requiring a real URL fetch or screenshot.

    Returns:
        verdict (str): PHISHING or BENIGN
        final_state (dict): full LangGraph end state
    """

    fake_url = attack_data["fake_url"]
    fake_domain = fake_url.split('/')[2] if "://" in fake_url else fake_url.split('/')[0]
    fake_html = attack_data["html_snippet"]
    fake_text = attack_data["page_text"]

    initial_state = {
        "webpage_data": {
            "url": fake_url,
            "domain": fake_domain,
            "html_content": fake_html,
            "cleaned_text": fake_text,
        },
        "screenshot": None,            # Visual not used in MVP (Phase-2 extension)
        "debate_history": [],
        "round_number": 0,
    }

    final_state = phish_guardian_app.invoke(initial_state)
    final_verdict = final_state.get("judge_verdict")

    return final_verdict, final_state



def attack_and_test(brand: str):
    """
    Generates a single phishing attempt against a brand and sends it to defender.

    Returns:
        verdict, attack_data, defender_state
    """
    raw_output = generate_phishing_variant(brand)

    # raw_output from attacker is JSON text → convert to dict
    try:
        attack_data = json.loads(raw_output)
    except Exception as e:
        raise ValueError(f"Attacker output must be valid JSON. Error: {e}")

    verdict, state = defend(attack_data)
    return verdict, attack_data, state



def evaluate_bypass_rate(brand: str, rounds: int = 20):
    """
    Runs stress tests to compute bypass rate against AEGIS.

    Bypass = defender fails to detect attack (verdict == BENIGN)
    Detection = defender succeeds (verdict == PHISHING)

    Printing output helps for research tables.
    """

    bypass_count = 0
    detection_count = 0

    for _ in range(rounds):
        raw_output = generate_phishing_variant(brand)

        try:
            attack_data = json.loads(raw_output)
        except Exception as e:
            print(f"[ERROR] Malformed attacker output: {e}")
            continue

        verdict, _ = defend(attack_data)

        if verdict == "BENIGN":
            bypass_count += 1
        else:
            detection_count += 1

    bypass_rate = (bypass_count / rounds) * 100
    detection_rate = (detection_count / rounds) * 100

    print("\n=== Adversarial Evaluation Report ===")
    print(f"Target Brand: {brand}")
    print(f"Total Rounds: {rounds}")
    print(f"Bypasses (FN): {bypass_count}")
    print(f"Detections (TP): {detection_count}")
    print(f"Bypass Rate: {bypass_rate:.2f}%")
    print(f"Detection Rate: {detection_rate:.2f}%")

    return {
        "brand": brand,
        "rounds": rounds,
        "bypass_count": bypass_count,
        "detection_count": detection_count,
        "bypass_rate": bypass_rate,
        "detection_rate": detection_rate
    }
