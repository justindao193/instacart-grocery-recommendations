# Instacart grocery recommendations

An independent learning project by Justin Dao. Not commissioned by, affiliated with or endorsed by Instacart.

![Prototype with a Buy it again row and a You might also like row](docs/images/prototype.jpg)

**Role:** Product manager & data analyst. I defined the scope, reviewed the evidence, made the trade-offs and facilitated two early prototype sessions.

**Question:** can a shopper's past orders help them find what they buy again, and suggest something new, better than a list of popular products?

## Results at a glance

| Version | What I tried | Result | Decision |
|---|---|---|---|
| 1. Buy it again | Compared 5 ways to rank familiar products on the same 131,209 shoppers | Weighted recency: 24.28% Recall@5, vs 23.12% personal frequency and 24.45% boosted trees | Kept weighted recency: a rule I can explain, at a small accuracy cost |
| 2. Purchase timing | Added a bonus when a product looked "due" | +0.025 points of recall, below the +0.25 bar set beforehand | Stopped and kept Version 1 |
| 3. You might also like | Ranked products absent from recorded history using shared buyers, against popular products | Held-back check (15,000 shoppers): Hit Rate@3 7.73% vs 6.63%, +1.10 points (95% range +0.69 to +1.51) | Added to the prototype |

The pass or fail check for Version 3 used three suggestions. The prototype shows five, which were measured afterwards on the same, already-seen shoppers (Hit Rate@5 10.77% vs 9.31%). Those five-item numbers describe the result; they are not a fresh test.

All scores are offline checks on past baskets. They do not show time saved, sales or retention.

## Review this project

- **Product story:** [case study](docs/case_study.md), [decisions](docs/decision_log.md), [user testing](docs/research_and_testing.md).
- **Working interface:** download and open [the shopping prototype](prototype/grocery_recommendations_prototype.html).
- **Readable code:** [portable ranking rules](src/recommendations.py) and [code walkthrough](docs/code_walkthrough.md).
- **Evidence:** [five-method comparison](results/final_evaluation.json) and [five-item discovery follow-up](results/discovery_top_five.json).
- **Process:** [how I tracked tasks, decisions and learning](docs/process_and_learning.md).

## Quick start

The reference example needs **Python 3.13 and no third-party packages or dataset**. It uses invented histories, clearly labelled as examples. It doesn't reproduce the full-data experiment or power the HTML prototype, which uses precomputed lists.

```bash
git clone https://github.com/justindao193/instacart-grocery-recommendations.git
cd instacart-grocery-recommendations
python run.py demo
python run.py results
python -m unittest discover -s tests -v
```

On Windows, use `py -3.13` instead of `python` if needed. `demo` prints example suggestions; `results` reads saved aggregates without retraining. Neither changes the original results.

The [shopping prototype](prototype/grocery_recommendations_prototype.html) runs in a browser without Python or an account. A/B use historical example profiles; C is a simulated shopper with no history.

## How the rules work

```text
Past orders -> weighted purchase history -> up to five familiar products
                       |
              top ten familiar products
                       |
     shared-buyer connections -> exclude familiar products
                       |
              up to five discovery products
```

A purchase contributes `0.5 ** (orders_since_purchase / 5)`: five order positions older means half the points. Discovery adds `seed_weight * connection_strength` across familiar products. Connection strength is `shared_buyers / sqrt(buyers_A * buyers_B)`. These are ranking points, not probabilities.

Hide filters familiar products before selecting five. A short familiar history stays short; a shopper without history gets popular products. Discovery excludes all recorded familiar products and uses unfamiliar popularity to fill remaining slots. See [the rule walkthrough](docs/code_walkthrough.md).

## Repository layout

| Path | Purpose |
|---|---|
| `run.py`, `src/recommendations.py` | Runnable reference of the selected rules |
| `tests/` | Behaviour checks, SQL fixture comparison and report checks |
| `.github/workflows/checks.yml` | Windows/Linux checks configured for pushes and pull requests |
| `prototype/` | Shopping page using saved recommendations |
| `src/data_preparation/` | Historical download, preparation and quality checks |
| `src/baselines/` | Historical popularity, frequency and weighted-recency Python/SQL |
| `src/model_comparison/` | Historical ML comparison, timing and discovery experiments |
| `src/final_evaluation/` | Historical prediction/scoring separation and discovery checks |
| `src/prototype_export/` | Historical exports from private prepared files |
| `results/` | Published aggregate evidence and protocols |
| `notebooks/` | Original walkthroughs; most cells need the private analysis layout |
| `docs/` | Case study, scope, methods, research, decisions, sources and code guide |

## Original analysis and reproducibility

The stage folders preserve the analysis behind the results. They still depend on original local paths, preparation reports and intermediate databases; they are **not a clean-clone pipeline**. The reference makes the rules runnable without claiming to repeat millions of records or the trained models.

Read [the dependency map and remaining gaps](docs/reproduction.md) for the full-data route. [requirements.txt](requirements.txt) records the original environment; installing it alone won't restore missing inputs. No raw orders, private databases or model files are committed.

The unit checks passed locally on Windows. The Windows/Linux GitHub workflow is configured, but a hosted pass isn't claimed until it runs. No models or final evaluations were rerun for this repository update.

## Process and learning

See [how I managed the decisions and learning](docs/process_and_learning.md) for the version-by-version process, task tracking and technical learning.

## How AI helped

I chose the problem, the scope of each version and the product direction, reviewed the methods and results, made the trade-offs and ran two exploratory user sessions. Codex helped write and check the SQL and Python, run the comparisons and keep the records. Claude helped design the prototype and the portfolio case study.

## Limits

- Two exploratory user sessions; they do not prove time saved. You might also like has not been tested with people.
- "New" means new to the shopper's recorded history.
- The data has no prices, pack sizes, stock or click records. The prototype has no real accounts, checkout or Instacart connection.

## Credits

Data: Instacart's 2017 "3 Million Instacart Orders" release, via a Zenodo archive. Prototype photos: [Unsplash](https://unsplash.com/license) and [Pexels](https://www.pexels.com/license/), showing the product type, not verified packaging. See [asset sources](docs/image_sources.json) for per-image references. The Instacart name and logo belong to Instacart.
