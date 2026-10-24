"""Build personal frequency, score validation and compare paired baseline results."""
# Load the Python tools used by this script.
from collections import defaultdict
from pathlib import Path
import json
import math
import duckdb

# Find the project folder so paths work from different starting locations.
ROOT = Path(__file__).resolve().parents[2]


# Build personal favourites and compare them with the saved popularity baseline.
def run_comparison():
    # Locate earlier validation scores; stop if the baseline has not been scored.
    output = ROOT / '02_Data/03_Model_Outputs'
    baseline_path = output / 'validation_popularity_scores.parquet'
    if not baseline_path.exists():
        raise FileNotFoundError('Run score_popularity_validation.py first.')
    # Load the SQL that ranks each customer's eligible past products.
    query = (ROOT / '03_Code/02_Baselines/personal_frequency.sql').read_text(encoding='utf-8')
    with duckdb.connect(str(ROOT / '02_Data/02_Prepared/instacart.duckdb'), read_only=True) as con:
        # Build the lists and reject duplicate products or ranks.
        recommendations = con.execute(query).df()
        assert not recommendations.duplicated(['user_id', 'product_id']).any()
        assert not recommendations.duplicated(['user_id', 'recommendation_rank']).any()
        assert recommendations.recommendation_rank.between(1, 5).all()
        con.register('personal_recommendations', recommendations)
        # Calculate matches, precision, recall and hit status for each validation basket.
        scores = con.execute('''
            SELECT e.user_id, e.validation_order_id,
                   COUNT(DISTINCT i.product_id) AS actual_products,
                   COUNT(DISTINCT CASE WHEN r.product_id IS NOT NULL THEN i.product_id END) AS matched_products,
                   matched_products / 5.0 AS precision_at_5,
                   matched_products * 1.0 / actual_products AS recall_at_5,
                   CAST(matched_products > 0 AS INTEGER) AS hit_at_5
            FROM evaluation_plan e
            JOIN order_products__prior i ON i.order_id = e.validation_order_id
            LEFT JOIN personal_recommendations r ON r.user_id=e.user_id AND r.product_id=i.product_id
            GROUP BY e.user_id, e.validation_order_id ORDER BY e.user_id
        ''').df()
        # Ensure both methods use exactly the same customers and actual baskets.
        baseline = con.read_parquet(str(baseline_path)).df().sort_values('user_id').reset_index(drop=True)
        for column in ['user_id', 'validation_order_id', 'actual_products']:
            assert scores[column].equals(baseline[column]), f'Comparison mismatch: {column}'
        assert scores.actual_products.gt(0).all()
        assert scores.matched_products.between(0, 5).all()
        assert scores.matched_products.le(scores.actual_products).all()
        for metric in ['precision_at_5', 'recall_at_5', 'hit_at_5']:
            assert scores[metric].between(0, 1).all()
        # Count filled suggestion slots; fewer than five products can be valid.
        counts = recommendations.groupby('user_id').size()
        assert len(counts) == len(scores)

        # Independently reconstruct ranking and scoring for 100 fixed customers.
        # Rebuild rankings and matches independently for 100 fixed customers.
        sample_ids = scores.head(100)[['user_id']]
        con.register('sample_users', sample_ids)
        histories = con.execute('''SELECT o.user_id, o.order_id, o.order_number, i.product_id
            FROM orders o JOIN evaluation_plan e USING(user_id)
            JOIN sample_users s USING(user_id)
            JOIN order_products__prior i USING(order_id)
            WHERE o.eval_set='prior' AND o.order_number<=e.validation_history_max_order_number
              AND o.order_id NOT IN (e.validation_order_id,e.final_target_order_id)''').fetchall()
        order_sets, latest = defaultdict(set), defaultdict(int)
        for uid, oid, order_number, pid in histories:
            order_sets[uid, pid].add(oid)
            latest[uid, pid] = max(latest[uid, pid], order_number)
        candidates = defaultdict(list)
        for uid, pid in order_sets:
            candidates[uid].append(pid)
        actual = defaultdict(set)
        for uid, pid in con.execute('''SELECT e.user_id,i.product_id FROM evaluation_plan e
            JOIN sample_users s USING(user_id)
            JOIN order_products__prior i ON i.order_id=e.validation_order_id''').fetchall():
            actual[uid].add(pid)
        predicted = recommendations.groupby('user_id').product_id.apply(list).to_dict()
        for row in scores.head(100).itertuples():
            uid = row.user_id
            expected = sorted(candidates[uid], key=lambda pid: (-len(order_sets[uid,pid]),-latest[uid,pid],pid))[:5]
            assert predicted[uid] == expected
            hits = len(set(expected) & actual[uid])
            assert hits == row.matched_products
            assert math.isclose(row.recall_at_5, hits / len(actual[uid]))
        # Check that no recommended product uses a purchase after the history cutoff.
        cutoffs = con.execute('SELECT user_id,validation_history_max_order_number FROM evaluation_plan').df()
        checked = recommendations.merge(cutoffs, on='user_id', validate='many_to_one')
        assert checked.last_purchase_order_number.le(checked.validation_history_max_order_number).all()

    # Save detailed recommendations and scores locally.
    output.mkdir(exist_ok=True)
    with duckdb.connect() as export:
        export.from_df(scores).write_parquet(str(output / 'validation_personal_frequency_scores.parquet'))
        export.from_df(recommendations).write_parquet(str(output / 'validation_personal_frequency_recommendations.parquet'))
    # Compare each customer's scores and estimate the uncertainty in the average difference.
    comparison = {}
    for metric in ['precision_at_5', 'recall_at_5', 'hit_at_5']:
        delta = scores[metric] - baseline[metric]
        comparison[metric] = {
            'popularity': float(baseline[metric].mean()),
            'personal_frequency': float(scores[metric].mean()),
            'difference_percentage_points': float(delta.mean() * 100),
            'paired_difference_approx_95pct_interval_pp': [
                float((delta.mean() - 1.96*delta.std(ddof=1)/math.sqrt(len(delta))) * 100),
                float((delta.mean() + 1.96*delta.std(ddof=1)/math.sqrt(len(delta))) * 100)
            ]
        }
    # Keep customer 1 as the teaching example, rather than choosing a flattering result.
    example = scores.loc[scores.user_id.eq(1)].iloc[0]
    # Record the comparison, short lists, checks and important limitations.
    report = {
        'stage': 'validation only; final train baskets untouched',
        'customers_evaluated': len(scores),
        'ranking': 'purchase-order count descending; latest purchase order descending; product_id ascending',
        'candidates': 'previously bought products only; no popularity filling; missing slots count against precision@5',
        'customers_with_fewer_than_five_suggestions': int((counts < 5).sum()),
        'comparison': comparison,
        'checks': {'independent_ranking_and_overlap_users': 100, 'matching_cohort_and_baskets': True, 'all_candidate_latest_purchases_before_validation': True},
        'example_user_1': {
            'suggestions': recommendations.loc[recommendations.user_id.eq(1)].to_dict(orient='records'),
            'actual_products': int(example.actual_products),
            'matched_products': int(example.matched_products)
        },
        'limits': 'Same targets, different candidate strategies: popularity can suggest unfamiliar products; personal is rebuy-only. Recency is only a tie-break, not a weighted-recency model. Approximate paired intervals describe sample uncertainty under independent-user assumptions, not population representativeness or causal benefit.'
    }
    # Save the summary report and return the tables.
    (ROOT / '05_Results/03_Checks/personal_frequency_validation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report, scores, recommendations


# Run this section only when the file is launched directly.
if __name__ == '__main__':
    report, _, _ = run_comparison()
    print(json.dumps(report, indent=2))
