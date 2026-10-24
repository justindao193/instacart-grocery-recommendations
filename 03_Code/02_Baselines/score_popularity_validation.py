"""Score the popularity baseline on validation only; leave final baskets untouched."""
# Load the Python tools used by this script.
from pathlib import Path
import json
import math
import duckdb

# Find the project folder so paths work from different starting locations.
ROOT = Path(__file__).resolve().parents[2]


# Build the general list, score validation baskets and save the results.
def score_validation():
    # Load the product-selection query and the separate scoring query.
    baseline_sql = (ROOT / '03_Code/02_Baselines/popularity_baseline.sql').read_text(encoding='utf-8')
    scoring_sql = (ROOT / '03_Code/02_Baselines/score_popularity_validation.sql').read_text(encoding='utf-8')
    with duckdb.connect(str(ROOT / '02_Data/02_Prepared/instacart.duckdb'), read_only=True) as con:
        # Build the list from eligible history and make it available to the scoring SQL.
        recommendations = con.execute(baseline_sql).df()
        assert len(recommendations) == 5 and recommendations.product_id.nunique() == 5
        con.register('validation_recommendations', recommendations)
        # Compare the five suggestions with each hidden validation basket.
        scores = con.execute(scoring_sql).df()
        # Check that every evaluation customer is scored once and all scores are valid.
        users = con.execute('SELECT user_id FROM evaluation_plan ORDER BY user_id').df()
        assert scores.user_id.tolist() == users.user_id.tolist(), 'Missing or duplicated customers'
        assert scores.validation_order_id.nunique() == len(scores)
        assert scores.actual_products.gt(0).all()
        assert scores.matched_products.between(0, 5).all()
        assert scores.matched_products.le(scores.actual_products).all()
        for metric in ['precision_at_5', 'recall_at_5', 'hit_at_5']:
            assert scores[metric].between(0, 1).all()

        # Independently reconstruct set overlap for the first 100 users.
        # Check the SQL scores independently using Python product sets.
        predicted = set(recommendations.product_id)
        sample = scores.head(100)
        con.register('sample_validation_users', sample[['user_id']])
        actual = con.execute('''SELECT e.user_id, i.product_id
            FROM evaluation_plan e JOIN sample_validation_users s USING(user_id)
            JOIN order_products__prior i ON i.order_id=e.validation_order_id''').fetchall()
        baskets = {}
        for user_id, product_id in actual:
            baskets.setdefault(user_id, set()).add(product_id)
        for row in sample.itertuples():
            basket = baskets[row.user_id]
            hits = len(basket & predicted)
            assert row.actual_products == len(basket) and row.matched_products == hits
            assert math.isclose(row.precision_at_5, hits / 5)
            assert math.isclose(row.recall_at_5, hits / len(basket))

        # Choose user 1 for teaching consistently, not based on a good score.
        example = scores.loc[scores.user_id.eq(1)].iloc[0]
        example_products = con.execute('''SELECT p.product_id, p.product_name
            FROM evaluation_plan e
            JOIN order_products__prior i ON i.order_id=e.validation_order_id
            JOIN products p ON p.product_id=i.product_id
            WHERE e.user_id=1 ORDER BY i.add_to_cart_order''').df()

    # Save customer-level scores locally, outside public Git history.
    output = ROOT / '02_Data/03_Model_Outputs'
    output.mkdir(exist_ok=True)
    with duckdb.connect() as export:
        export.from_df(scores).write_parquet(str(output / 'validation_popularity_scores.parquet'))
    # Summarise average precision, recall and the share of customers with any match.
    report = {
        'stage': 'validation only; official train final baskets not scored',
        'method': 'same five popular products for every evaluated customer',
        'customers_evaluated': len(scores),
        'customers_with_at_least_one_match': int(scores.hit_at_5.sum()),
        'mean_precision_at_5': float(scores.precision_at_5.mean()),
        'mean_recall_at_5': float(scores.recall_at_5.mean()),
        'hit_rate_at_5': float(scores.hit_at_5.mean()),
        'mean_matches_per_customer': float(scores.matched_products.mean()),
        'averaging': 'mean of per-customer scores; same cohort required for future methods',
        'checks': {'all_evaluation_users_present': True, 'independent_set_overlap_users': 100},
        'example_user_1': {
            'actual_products': int(example.actual_products),
            'matched_products': int(example.matched_products),
            'precision_at_5': float(example.precision_at_5),
            'recall_at_5': float(example.recall_at_5),
            'basket': example_products.to_dict(orient='records')
        },
        'limits': 'Offline purchase overlap, not causal benefit. Per-user sequence holdout, not calendar backtest. No comparison winner declared.'
    }
    # Save the aggregate report and return scores for notebooks.
    (ROOT / '05_Results/03_Checks/popularity_validation_scores.json').write_text(
        json.dumps(report, indent=2), encoding='utf-8'
    )
    return report, scores


# Run this section only when the file is launched directly.
if __name__ == '__main__':
    report, _ = score_validation()
    print(json.dumps(report, indent=2))
