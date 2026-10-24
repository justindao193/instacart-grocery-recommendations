# Grocery recommendations from public Instacart orders

An independent learning project by Justin Dao. Not commissioned by, affiliated with or endorsed by Instacart.

![Prototype with a Buy it again row and a You might also like row](docs/images/prototype.jpg)

**Question:** can a shopper's past orders help them find what they buy again, and suggest something new, better than a list of popular products?

## Results at a glance

| Version | What I tried | Result | Decision |
|---|---|---|---|
| 1. Buy it again | Compared 5 ways to rank familiar products on the same 131,209 shoppers | Weighted recency: 24.28% Recall@5, vs 23.12% personal frequency and 24.45% boosted trees | Kept weighted recency: a rule I can explain, at a small accuracy cost |
| 2. Purchase timing | Added a bonus when a product looked "due" | +0.025 points of recall, below the +0.25 bar set beforehand | Stopped and kept Version 1 |
| 3. You might also like | Ranked products absent from recorded history using shared buyers, against popular products | Held-back check (15,000 shoppers): Hit Rate@3 7.73% vs 6.63%, +1.10 points (95% range +0.69 to +1.51) | Added to the prototype |

The pass or fail check for Version 3 used three suggestions. The prototype shows five, which were measured afterwards on the same, already-seen shoppers (Hit Rate@5 10.77% vs 9.31%). Those five-item numbers describe the result; they are not a fresh test.

All scores are offline checks on past baskets. They do not show time saved, sales or retention.

## Repository layout

| Folder | What is inside |
|---|---|
| `prototype/` | `grocery_recommendations_prototype.html`, the clickable shopping page. Open it in any browser. |
| `src/data_preparation/` | Download the data, prepare it and check it |
| `src/baselines/` | Popularity, personal frequency and weighted recency (Python + SQL) |
| `src/model_comparison/` | Machine learning models, the Version 2 timing test and Version 3 discovery |
| `src/final_evaluation/` | The one-time final check for Version 1 and the held-back check for Version 3 |
| `src/prototype_export/` | Export saved example lists and photos into the prototype |
| `results/` | Summary reports behind every number above |
| `notebooks/` | Three walkthrough notebooks |
| `docs/` | Case study, project brief, data and methods, research and testing, decision log |

## Key code

- Weighted recency (recent purchases count more; the weight halves every five orders): [`src/baselines/score_weighted_recency.py`](src/baselines/score_weighted_recency.py), [`weighted_recency.sql`](src/baselines/weighted_recency.sql)
- Discovery with shared buyers: [`src/model_comparison/evaluate_discovery.py`](src/model_comparison/evaluate_discovery.py)
- Five-item descriptive follow-up: [`src/final_evaluation/measure_discovery_top_five.py`](src/final_evaluation/measure_discovery_top_five.py)
- Held-back discovery check: [`src/final_evaluation/evaluate_discovery_audit.py`](src/final_evaluation/evaluate_discovery_audit.py)

## Running it

**Try the prototype:** download this repository, then open [Grocery Recommendations](prototype/grocery_recommendations_prototype.html) in a browser. No Python or account is required. A/B are historical example profiles; C is a simulated no-history profile.

**Read the evidence:** the [case study](docs/case_study.md) and saved JSON files in `results/` are available without running analysis.

**Analysis prerequisites:** the scripts and most notebook cells need the six Instacart CSVs (about 700 MB), which are not included. Get them from the [Zenodo archive](https://zenodo.org/records/2654444) of the 2017 [Instacart release](https://tech.instacart.com/3-million-instacart-orders-open-sourced-d40d29ead6f2) and check the dataset's terms before use.

```
py -3.13 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Analysis-code status

This is a curated **historical code snapshot**, not a self-contained reproducible pipeline. Relocating files into `src/` left original path assumptions and hash dependencies intact. Some scripts need omitted preparation reports, evaluation metadata and private intermediate databases in addition to source CSVs. For example, the audit script currently imports from the original `03_Code/` path, so even its `--help` fails in this layout. Merely recreating the data folders is insufficient.

The code is published for inspection and provenance. End-to-end reproduction needs an explicit path migration, a complete dependency/build-order map and a separate clean-environment check. Do not edit historical hashes or present a rerun on exposed answers as a new test. See [repository review](docs/repository_review.md) for the concrete gaps.

Notes:
- The scripts are kept exactly as they were run, so file paths inside them follow the original project layout (`02_Data/` for data, `05_Results/03_Checks/` for reports, `03_Code/<stage>/` for code). Recreate those folders, or update the paths, before rerunning.
- Built and checked on one Windows machine with Python 3.13. A fresh setup on another computer has not been tested.
- The final checks have already been opened, so rerunning them is not a fresh test.

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
