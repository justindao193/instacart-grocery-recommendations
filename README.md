# Grocery recommendations: Buy it again and You might also like, from public Instacart orders

An independent learning project by Justin Dao. It is not commissioned by, affiliated with or endorsed by Instacart.

**Question:** can a short list of familiar products help returning grocery shoppers find what they buy again, with less searching? And later: can past purchases suggest unfamiliar products better than a list of popular ones?

**Case study:** see the Grocery recommendations project on my portfolio (link to be added once the portfolio is public).

## What is in this repository

| Version | What I tried | Result | Decision |
|---|---|---|---|
| V1 Buy it again | Compared 5 ways to rank familiar products on the same 131,209 shoppers | Weighted recency: 24.28% Recall@5 vs 23.12% personal frequency and 24.45% boosted trees | Kept weighted recency, a simple rule I can trace, and accepted the small accuracy gap to trees |
| V2 Purchase timing | Added one fixed timing bonus to weighted recency (60,000 development shoppers) | +0.025 points of recall, below the +0.25 bar set beforehand; interval included zero | Stopped. Kept the simpler rule |
| V3 Discovery | Ranked unfamiliar products using shared buyers, against unfamiliar popularity | Reserved check (15,000 shoppers): Hit Rate@3 7.727% vs 6.627%, +1.100 points (approx. 95% interval +0.693 to +1.507) | Added a "You might also like" section to the prototype |

All scores are offline checks against historical baskets. They are not evidence of time saved, sales or retention.

**Three first, then five.** The pass or fail check above used the top **three** suggestions. The prototype later moved to **five** cards from the same ranking. Five suggestions were then measured on the same shoppers with no tuning: on the 15,000 reserved shoppers, Hit Rate@5 was 10.773% vs 9.313% (+1.46 points, approx. 95% interval +1.02 to +1.90). Those answers had already been seen, so the five-item numbers are descriptive, not a fresh test (`05_Results/03_Checks/discovery_top_five.json`).

## What runs from this repository alone

| Item | Runs without the dataset? |
|---|---|
| `03_Code/05_Prototype/buy_again_prototype.html` | **Yes.** Open it in a browser. It is self-contained, with saved example lists and embedded photos. It does not run Python or retrain anything. |
| `05_Results/03_Checks/*.json` | **Yes.** Aggregate evidence reports for every check and result. |
| Project documents (`01_Project/`, `04_Learning/`, `05_Results/`) and `00_START_HERE.html` | **Yes.** Read in any browser or Markdown viewer. |
| SQL and Python in `03_Code/01` to `03_Code/04` | **No.** They need the Instacart CSVs (about 700 MB) and the prepared local databases, which are not included. |
| Notebooks in `04_Learning/03_Notebooks/` | Partly. Some cells show saved aggregate results; most need the local data. |

## Setup (to rerun the analysis)

This was built and checked on one Windows machine with Python 3.13. A fresh install on another computer has **not** been tested end to end.

1. Install Python 3.13.
2. From the repository root, run `03_Code\00_Run\01_Setup_Python.bat`, or:
   ```
   py -3.13 -m venv .venv
   .venv\Scripts\python.exe -m pip install -r 03_Code\00_Run\requirements-lock.txt
   ```
3. Get the data: `.venv\Scripts\python.exe 03_Code\01_Data_Preparation\download_data.py` downloads the six CSVs from the [Zenodo archive](https://zenodo.org/records/2654444) of the 2017 [Instacart release](https://tech.instacart.com/3-million-instacart-orders-open-sourced-d40d29ead6f2) into `02_Data/01_Original/` and checks their checksums. Check the dataset's terms before use.
4. Follow `03_Code/README.md` for the stage-by-stage scripts.

Notes:
- Current feature work uses Python and SQLite. Some older scripts and notebook cells use DuckDB, which Windows Smart App Control blocked on my machine. Those older routes may fail.
- Do not rerun the final evaluation or the discovery audit as if they were fresh tests. Their answers have already been opened. The discovery and timing scripts refuse to overwrite saved results for this reason.

## Key code

| What | Where |
|---|---|
| Weighted recency ranking (recent purchases count more; weight halves every 5 orders) | `03_Code/02_Baselines/score_weighted_recency.py`, `03_Code/02_Baselines/weighted_recency.sql` |
| Machine learning comparison (logistic regression, boosted trees) | `03_Code/03_Model_Comparison/train_logistic_validation.py`, `build_ml_features.py` |
| V2 timing experiment | `03_Code/03_Model_Comparison/evaluate_purchase_timing.py` |
| V3 discovery, development comparison | `03_Code/03_Model_Comparison/evaluate_discovery.py` |
| V3 discovery, reserved check | `03_Code/04_Final_Evaluation/evaluate_discovery_audit.py` |
| Final V1 evaluation | `03_Code/04_Final_Evaluation/prepare_final_predictions.py`, `score_final_predictions.py` |
| Prototype | `03_Code/05_Prototype/buy_again_prototype.html` |

## Folder map

| Folder | Contents |
|---|---|
| `00_START_HERE.html` | Project guide with the task board, learning path and readable findings. Task progress is saved in the browser, so a fresh copy shows the starting backlog, not my current progress. |
| `01_Project/` | Brief, learning path, data and methods, research and testing record, case study, project checkpoint, prototype requirements, brand guide |
| `02_Data/` | READMEs only. Raw data, prepared databases and model outputs are excluded. |
| `03_Code/` | Numbered stages: data preparation, baselines, model comparison, final evaluation, prototype, guide |
| `04_Learning/` | Learning notes, dated learning log and three grouped notebooks |
| `05_Results/` | Findings, decision log and aggregate check reports |

## How I worked, and how AI helped

I chose the problem, the scope of each version and the product direction. I reviewed the methods and results, made the trade-offs (for example, weighted recency over boosted trees, and stopping V2), gave design feedback and ran two exploratory user sessions.

AI tools did a large part of the implementation:
- **Codex** helped write and check the SQL and Python, run the comparisons, explain concepts, and keep the documents and logs organised.
- **Claude** helped design the HTML prototype and its brand guide, and build the portfolio case study.

I do not claim I wrote every component independently. `AGENTS.md` holds the working rules I gave the AI tools. It is an instruction file; it does not train a model. The learning log shows what I worked through and when.

## Limits

- The two user sessions were exploratory. They do not prove the feature saves time. Discovery has not been tested with people.
- "New" product means new to the shopper's recorded history, not a proven first-ever purchase.
- The data has no prices, quantities, browsing or recommendation exposure, so no revenue or engagement impact is claimed.
- The prototype has no real accounts, checkout, prices, stock or Instacart connection. Nothing is deployed.

## Credits

- Data: Instacart's 2017 public "3 Million Instacart Orders" release, retrieved from a [Zenodo archive](https://zenodo.org/records/2654444).
- Product photos in the prototype: [Unsplash](https://unsplash.com/license), illustrative of the product type, not the exact package. Sources and hashes: `01_Project/Assets/prototype_image_sources.json`.
- The Instacart name, logo and colours are used only to frame this independent study and belong to Instacart.
