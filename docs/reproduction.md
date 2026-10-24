# Running and reproducing the project

## Runs from this repository

| Command or file | Inputs | What it establishes |
|---|---|---|
| `python run.py demo` | Invented fixture inside `run.py` | Runnable example of the selected rules |
| `python run.py results` | Published JSON reports | Read existing aggregates without retraining |
| `python -m unittest discover -s tests -v` | Small fixtures, original SQL and reports | Behaviour checks, not a repeat of the full evaluation |
| `prototype/grocery_recommendations_prototype.html` | Embedded examples/photos and a browser | Interface with historical A/B examples and simulated C |

Python 3.13 is the checked local interpreter. No package installation is needed for these commands. GitHub Actions is configured for Windows and Linux; hosted checks remain pending publication. The optional Google font needs internet; a local font is used if unavailable.

## Historical full-data dependency map

This is an input/output map, **not a validated sequence of commands for a fresh clone**. Several intermediate builders and provenance inputs aren't included. Restoring the original directory names alone is insufficient.

| Stage | Code | Required inputs | Outputs and current gaps |
|---|---|---|---|
| Retrieve | `src/data_preparation/download_data.py` | Archive URLs and source manifest | Six raw CSVs |
| Prepare/check | `src/data_preparation/` | CSVs in original `02_Data/01_Original/` layout | DuckDB, evaluation plan, preparation manifests; verification also expects the original guide/notebook paths |
| Baselines | `src/baselines/` | Checked database, evaluation plan, SQL at original `03_Code/` paths | Validation predictions and reports; original path assumptions remain |
| ML features/models | `src/model_comparison/build_ml_features.py` and training scripts | Plan, earlier CSVs, baseline reports, checked preparation marker | SQLite features, model files, validation reports; private intermediates aren't included |
| V1 final check | `src/final_evaluation/prepare_final_predictions.py`, `score_final_predictions.py` | Checked features, frozen models/code, protocol; source train answers only during scoring | Predictions saved before final scoring; needs unpublished preparation metadata and models |
| V2 timing | `src/model_comparison/evaluate_purchase_timing.py` | Timing database and preparation report | Timing comparison; timing preparation builder/database isn't included |
| V3 discovery | `src/model_comparison/prepare_discovery_baseline.py`, `evaluate_discovery.py` | Timing SQLite, checked metadata, fixed cohort, history-only popularity | Connections and development predictions/report; not runnable from CSVs alone here |
| V3 audit/follow-up | `src/final_evaluation/evaluate_discovery_audit.py`, `measure_discovery_top_five.py` | Frozen outputs, prior CSV, protocols and fingerprint inputs | Audit and descriptive follow-up; audit import still uses old `03_Code/` path |
| Interface export | `src/prototype_export/` | Prepared databases, product metadata and saved rankings | Embedded example lists/photos; published HTML already contains the export |

The original environment snapshot is [requirements.txt](../requirements.txt), not a minimal list for the reference example. DuckDB's native binary was blocked on the original Windows setup; later ML preparation used SQLite. The reference example doesn't need DuckDB.

## Data and evidence boundaries

- Sources: [Instacart's 2017 release](https://tech.instacart.com/3-million-instacart-orders-open-sourced-d40d29ead6f2), [dictionary](https://gist.github.com/jeremystan/c3b39d947d9b88b3ccff3147dbcf6c6b), [usage terms](https://gist.github.com/jeremystan/582eba13d6ee27ed465c43dc78934700).
- Working files came from [Zenodo](https://zenodo.org/records/2654444). The [source manifest](../results/source_manifest.json) records provenance and checksums. Identity with unavailable original publisher bytes isn't claimed.
- These selected historical records aren't representative of all shoppers. Prices, quantities, stock and browsing/click exposures aren't available.
- Preserve protocols and results. A portability change doesn't make inspected baskets fresh. Don't alter fingerprints to make an old evaluation appear to pass.
- Raw CSVs, private databases, environments and credentials stay out of commits. Dataset, image and trademark rights are separate from project code.

## Remaining reproduction work

A complete rebuild needs omitted preparation builders/metadata, explicit path migration with historical hash mapping, and a clean-environment end-to-end run. That work isn't complete. The reference and tests don't claim to solve it. No ML model or historical evaluation is rebuilt by the quick start.
