"""Data-free entry point: inspect rules or read saved aggregate evidence."""
import argparse
import json
from pathlib import Path
from src.recommendations import (Purchase, basket_metrics, build_connections,
                                 discovery_products, familiar_products)

ROOT = Path(__file__).resolve().parent


def demo() -> dict:
    """Use invented tiny histories to explain the logic, never as project results."""
    names = {1: "Eggs", 2: "Milk", 3: "Bread", 4: "Apples", 5: "Oats", 6: "Bananas"}
    history = [Purchase(1, 1), Purchase(2, 1), Purchase(1, 2), Purchase(1, 3)]
    # Tiny fixture needs lower support counts than the full-data 50/5 thresholds.
    links = build_connections([{1, 3, 4}, {1, 3, 5}, {1, 4}, {2, 5, 6}],
                              min_buyers=1, min_shared=1)
    popular = [1, 3, 4, 5, 6, 2]
    familiar = familiar_products(history, 3, popularity=popular)
    discovery = discovery_products(history, 3, links, popular)
    return {"example": "Invented teaching fixture, not measured Instacart performance",
            "buy_it_again": [names[pid] for pid in familiar],
            "you_might_also_like": [names[pid] for pid in discovery],
            "toy_next_basket": ["Eggs", "Apples", "Bread"],
            "familiar_toy_metrics_at_5": basket_metrics(familiar, [1, 4, 3])}


def saved_results() -> dict:
    """Read published aggregates only; don't open customer data or rerun scoring."""
    final = json.loads((ROOT / "results/final_evaluation.json").read_text(encoding="utf-8"))
    discovery = json.loads((ROOT / "results/discovery_top_five.json").read_text(encoding="utf-8"))
    return {"v1_shoppers": final["customers"], "v1_final_metrics": final["overall"],
            "discovery_top_five_note": discovery["interpretation"],
            "discovery_top_five_15000_shoppers": discovery["stages"]["audit"]["overall"],
            "limits": "Historical basket matches; no proof of shopping time saved or sales lift"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("demo", "results"),
                        help="demo: invented example; results: saved aggregate evidence")
    args = parser.parse_args()
    print(json.dumps(demo() if args.command == "demo" else saved_results(), indent=2))


if __name__ == "__main__":
    main()
