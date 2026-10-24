# Code walkthrough

Start with [the runnable reference](../src/recommendations.py). It expresses the selected rules with small, named functions. It was added after the experiments to make review easier; it wasn't used to produce the saved project metrics.

## Follow one shopper

1. `Purchase` describes one product in one order, not units bought.
2. `_earlier` removes orders after the history cutoff and counts each order/product pair once.
3. `weighted_history` adds purchase points. A purchase at the cutoff earns 1 point; one five order positions older earns 0.5. It sorts by score, latest purchase, then product ID.
4. `familiar_products` removes hidden IDs, then takes up to five. A short personal list stays short. With no history, it uses popularity instead.
5. `build_connections` finds products bought by the same people. One shopper counts as one buyer, regardless of repeats. Connection strength is shared buyers divided by the square root of the two buyer counts. Full-data defaults require 50 buyers, 5 shared buyers and at most 40 neighbours per product.
6. `discovery_products` takes the ten highest-ranked familiar products. Each contributes its history score times connection strength to unfamiliar candidates. All familiar products are excluded, including those outside the ten seeds. Product ID breaks ties; unfamiliar popularity fills gaps.
7. `basket_metrics` checks a chosen list against one known later basket. That basket isn't passed to the ranking functions.

The reference connection builder uses simple pairwise comparisons for small fixtures. The original [discovery experiment](../src/model_comparison/evaluate_discovery.py) uses sparse matrices and batching for scale. The invented CLI example lowers support thresholds for its tiny fixture; those settings aren't new validation evidence.

## What the measurements mean

For five suggestion slots, if two suggestions appear in a ten-product basket:

| Measure | Calculation | Meaning |
|---|---|---|
| Precision@5 | 2 / 5 = 40% | How many suggestions matched? |
| Recall@5 | 2 / 10 = 20% | How much of the actual basket did we find? |
| Hit@5 | 1 | Was there any match? Average across shoppers for hit rate. |

Precision still divides by five for a short list. Recall uses the complete basket, including products outside personal history. The discovery reports also contain separate novel-product recall with its own denominator; don't substitute it for whole-basket recall.

## Where the original code lives

| Review question | File | What to look for |
|---|---|---|
| Where does the selected score come from? | [Weighted SQL](../src/baselines/weighted_recency.sql) | Cutoff, half-life, tie-breaking |
| How were models challenged? | [Logistic regression](../src/model_comparison/train_logistic_validation.py), [trees](../src/model_comparison/train_boosted_validation.py) | Training inputs, fixed settings, later validation |
| How did discovery scale? | [Discovery](../src/model_comparison/evaluate_discovery.py) | Buyer matrix, support gates, seeds, exclusions |
| Were final answers kept separate? | [Prepare lists](../src/final_evaluation/prepare_final_predictions.py), [score lists](../src/final_evaluation/score_final_predictions.py) | Save lists first; verify hashes before scoring |
| What supports the five-card display? | [Top-five follow-up](../src/final_evaluation/measure_discovery_top_five.py) | Exposed-data caveat; no new model |
| What do checks protect? | [Tests](../tests/test_recommendations.py) | Cutoffs, ties, hiding, buyer counts, fallback, denominators |

The original Python and SQL already contain section comments. Those files are preserved because protocols reference their historical fingerprints. This guide explains them without changing the code identified by those reports.

The HTML prototype uses saved example lists. The reference CLI is separate; it isn't a new serving backend or a model retraining step.
