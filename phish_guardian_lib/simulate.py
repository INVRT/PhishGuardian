# simulate.py

import csv
from phish_guardian_lib.simulator import attack_and_test
from phish_guardian_lib.learning.weighting import print_agent_weights
import matplotlib.pyplot as plt


def evaluate_training_curve(brand: str, cycles: int = 10, attacks_per_cycle: int = 10):
    """
    Runs multi-cycle adversarial training to measure detection/bypass performance over time.
    """
    results = []

    for cycle in range(cycles):
        bypass = 0
        detect = 0

        for _ in range(attacks_per_cycle):
            verdict, _, _ = attack_and_test(brand)
            if verdict == "BENIGN":
                bypass += 1
            else:
                detect += 1

        bypass_rate = (bypass / attacks_per_cycle) * 100
        detect_rate = 100 - bypass_rate

        print(f"[Cycle {cycle+1}] Bypass: {bypass_rate:.2f}% | Detect: {detect_rate:.2f}%")
        print_agent_weights()

        results.append({
            "cycle": cycle + 1,
            "bypass_rate": bypass_rate,
            "detect_rate": detect_rate
        })

    return results



def plot_training_curve(results, brand: str):
    x = [r['cycle'] for r in results]
    y_detect = [r['detect_rate'] for r in results]
    y_bypass = [r['bypass_rate'] for r in results]

    plt.figure(figsize=(8,5))
    plt.plot(x, y_detect, marker='o', label="Detection Rate")
    plt.plot(x, y_bypass, marker='o', label="Bypass Rate")
    plt.title(f"AEGIS Adversarial Hardening Curve ({brand})")
    plt.xlabel("Training Cycle")
    plt.ylabel("Rate (%)")
    plt.grid(True)
    plt.legend()
    plt.show()



def export_results(results, filename="training_curve.csv"):
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["cycle", "bypass_rate", "detect_rate"])
        writer.writeheader()
        writer.writerows(results)
    print(f"Results exported to {filename}")
