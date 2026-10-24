# Prepared data

`03_Code/prepare_data.py` builds these tables from the unchanged source CSVs. If a preparation rule changes, I'll update the script and rebuild rather than edit generated rows by hand.

The databases hold large tables so the learning notebook can stay small. Start with `learning_orders.csv` and `learning_order_items.csv`.

For current ML preparation, `03_Code/build_ml_features.py` uses Python's built-in SQLite engine and writes `instacart_ml.sqlite`. It contains only the evaluation cohort's prior orders through validation and the training/validation feature rows. Official final basket contents aren't imported. Check `05_Results/03_Checks/ml_feature_preparation.json` and the database's `features_checked` marker before using these features.

The existing `instacart.duckdb` and earlier DuckDB scripts are retained for historical reproducibility. Windows Smart App Control currently blocks DuckDB on this computer; the SQLite preparation doesn't depend on it. This is a switch for ML preparation, not a claim that every old notebook cell has been converted.

Descriptive product and department metrics use prior orders only. The labelled final baskets stay separate for later evaluation. Test baskets have unknown contents, represented by blank summary counts.

`evaluation_plan.csv` identifies the earlier validation cutoff and later final target. It doesn't contain predictions or evaluation scores. The findings are still open.
