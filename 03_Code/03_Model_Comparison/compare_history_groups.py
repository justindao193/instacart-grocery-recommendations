"""Exploratory validation comparison by pre-target history length."""
# Load the Python tools used by this script.
from pathlib import Path
import json
import math
import duckdb

# Find the project folder so paths work from different starting locations.
ROOT = Path(__file__).resolve().parents[2]


# Compare existing validation results by the amount of earlier history.
def compare_groups():
    # Define the groups before inspecting their scores.
    groups = [('Short: 1–5 orders', 1, 5), ('Medium: 6–15 orders', 6, 15),
              ('Long: 16+ orders', 16, None)]
    output = ROOT / '02_Data/03_Model_Outputs'
    with duckdb.connect(str(ROOT / '02_Data/02_Prepared/instacart.duckdb'), read_only=True) as con:
        # Read both saved score tables and match the same customers and baskets.
        personal = con.read_parquet(str(output / 'validation_personal_frequency_scores.parquet')).df()
        popular = con.read_parquet(str(output / 'validation_popularity_scores.parquet')).df()
        merged = personal.merge(popular, on=['user_id', 'validation_order_id', 'actual_products'],
                                suffixes=('_personal', '_popular'), validate='one_to_one')
        assert len(merged) == len(personal) == len(popular)
        # Count only orders available before each customer's validation basket.
        history = con.execute('''SELECT e.user_id, COUNT(DISTINCT o.order_id) AS history_orders
            FROM evaluation_plan e JOIN orders o ON o.user_id=e.user_id
            WHERE o.eval_set='prior' AND o.order_number<=e.validation_history_max_order_number
            GROUP BY e.user_id''').df()
        # Count how many suggestion slots each customer actually received.
        recs = con.read_parquet(str(output / 'validation_personal_frequency_recommendations.parquet')).df()
        slots = recs.groupby('user_id').size().rename('suggestions').reset_index()
        merged = merged.merge(history, on='user_id', validate='one_to_one')
        merged = merged.merge(slots, on='user_id', validate='one_to_one')
        assert len(merged) == con.execute('SELECT COUNT(*) FROM evaluation_plan').fetchone()[0]
        assert merged.history_orders.ge(1).all()

    # Create one summary per history group, with no customer assigned twice.
    summaries = []
    assigned = set()
    for name, low, high in groups:
        subset = merged.loc[merged.history_orders.ge(low)]
        if high is not None:
            subset = subset.loc[subset.history_orders.le(high)]
        assert len(subset) > 0
        ids = set(subset.user_id)
        assert not assigned.intersection(ids)
        assigned.update(ids)
        # Calculate the personal-versus-general recall difference within this group.
        delta = subset.recall_at_5_personal - subset.recall_at_5_popular
        summary = {
            'group': name, 'history_min': low, 'history_max': high,
            'customers': len(subset),
            'mean_actual_basket_products': float(subset.actual_products.mean()),
            'customers_with_fewer_than_five_suggestions': int(subset.suggestions.lt(5).sum()),
            'mean_suggestions': float(subset.suggestions.mean()),
            'recall_gain_percentage_points': float(delta.mean()*100),
            'paired_recall_gain_approx_95pct_interval_pp': [
                float((delta.mean()-1.96*delta.std(ddof=1)/math.sqrt(len(subset)))*100),
                float((delta.mean()+1.96*delta.std(ddof=1)/math.sqrt(len(subset)))*100)]
        }
        for method in ['popular', 'personal']:
            for metric in ['precision_at_5', 'recall_at_5', 'hit_at_5']:
                summary[f'{method}_{metric}'] = float(subset[f'{metric}_{method}'].mean())
        summaries.append(summary)
    # Check that the groups cover everyone and recover the overall averages.
    assert len(assigned) == len(merged)
    for method in ['popular', 'personal']:
        for metric in ['precision_at_5', 'recall_at_5', 'hit_at_5']:
            weighted = sum(s['customers']*s[f'{method}_{metric}'] for s in summaries)/len(merged)
            assert math.isclose(weighted, merged[f'{metric}_{method}'].mean())
    # Save group counts, scores and caveats; the comparison is not a causal experiment.
    report = {
        'stage': 'exploratory validation segmentation; no final baskets scored',
        'grouping': 'count of eligible prior orders before the validation basket; 1–5, 6–15, 16+',
        'customers_evaluated': len(merged),
        'groups': summaries,
        'checks': 'All cohort users assigned once; same target baskets; weighted groups recover overall scores.',
        'limits': 'Observed groups are not randomised. History length can coincide with different basket sizes and habits. No zero-history users are evaluated. Paired intervals assume independent users and do not establish representativeness.'
    }
    (ROOT / '05_Results/03_Checks/history_group_validation.json').write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    return report


# Run this section only when the file is launched directly.
if __name__ == '__main__':
    print(json.dumps(compare_groups(), indent=2, ensure_ascii=False))
