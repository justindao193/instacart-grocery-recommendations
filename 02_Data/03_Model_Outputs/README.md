# Model outputs

Generated customer-level outputs stay here and are excluded from public Git history.

`validation_popularity_scores.parquet` has one row per evaluated customer, with the validation order, actual basket size, matches and precision/recall/hit scores. Rebuild it using `03_Code/score_popularity_validation.py` from the project root with the project's Python environment.

These are validation scores. Final evaluation hasn't been run. Keep customer-level records local; use aggregate summaries for the portfolio.

`validation_personal_frequency_scores.parquet` stores scores for the same customers and baskets. `validation_personal_frequency_recommendations.parquet` stores their ranked personal suggestions. Rebuild both with `03_Code/score_personal_frequency.py`. It compares them with the saved popularity scores and verifies cohort/target alignment.
