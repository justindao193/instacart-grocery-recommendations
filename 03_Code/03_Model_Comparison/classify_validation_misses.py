"""Diagnose rebuy-only misses; do not use diagnostic targets as model features."""
# Load the Python tools used by this script.
from pathlib import Path
import json
import math
import duckdb

# Find the project folder so paths work from different starting locations.
ROOT = Path(__file__).resolve().parents[2]


# Separate missed familiar products from products absent from the earlier history.
def classify_misses():
    # Load the diagnostic SQL and locate saved personal recommendations.
    query = (ROOT / '03_Code/03_Model_Comparison/classify_validation_misses.sql').read_text(encoding='utf-8')
    output = ROOT / '02_Data/03_Model_Outputs'
    with duckdb.connect(str(ROOT / '02_Data/02_Prepared/instacart.duckdb'), read_only=True) as con:
        # Read personal lists and ensure the same product is not suggested twice.
        recs = con.read_parquet(str(output / 'validation_personal_frequency_recommendations.parquet')).df()
        assert not recs.duplicated(['user_id', 'product_id']).any()
        con.register('personal_recommendations', recs)
        # Classify the hidden basket after prediction, then compare with saved scores.
        diagnostic = con.execute(query).df()
        scores = con.read_parquet(str(output / 'validation_personal_frequency_scores.parquet')).df().sort_values('user_id').reset_index(drop=True)
        for column in ['user_id','validation_order_id','actual_products','matched_products']:
            assert diagnostic[column].equals(scores[column]), column
        assert diagnostic.invalid_new_matches.eq(0).all()
        assert diagnostic.actual_products.eq(diagnostic.known_products+diagnostic.new_products).all()
        assert diagnostic.known_misses.eq(diagnostic.known_misses_beyond_five_slot_capacity+diagnostic.recoverable_with_perfect_rebuy_ranking).all()
        assert diagnostic.recoverable_with_perfect_rebuy_ranking.ge(0).all()
        assert diagnostic.perfect_rebuy_recall_at_5.ge(scores.recall_at_5).all()

    # Add the product-line counts and check that hits and misses cover every line.
    total = int(diagnostic.actual_products.sum())
    hits = int(diagnostic.matched_products.sum())
    known_misses = int(diagnostic.known_misses.sum())
    new = int(diagnostic.new_products.sum())
    missed = total-hits
    assert hits+known_misses+new == total
    # Calculate actual recall and a hindsight-only ceiling for a perfect rebuy ranking.
    mean_recall = float((diagnostic.matched_products/diagnostic.actual_products).mean())
    ceiling = float(diagnostic.perfect_rebuy_recall_at_5.mean())
    assert math.isclose(mean_recall, float(scores.recall_at_5.mean()))
    # Record miss shares, their denominators and the limits of this diagnosis.
    report = {
        'stage': 'validation diagnosis only; final baskets untouched',
        'customers': len(diagnostic),
        'total_actual_product_lines': total,
        'matched_product_lines': hits,
        'missed_product_lines': missed,
        'known_product_misses': known_misses,
        'new_product_misses': new,
        'pct_of_missed_lines_known': 100*known_misses/missed,
        'pct_of_missed_lines_new': 100*new/missed,
        'known_misses_beyond_five_slot_capacity': int(diagnostic.known_misses_beyond_five_slot_capacity.sum()),
        'known_misses_recoverable_with_perfect_ranking': int(diagnostic.recoverable_with_perfect_rebuy_ranking.sum()),
        'mean_personal_recall_at_5': mean_recall,
        'mean_perfect_rebuy_recall_at_5': ceiling,
        'mean_recall_gap_to_perfect_rebuy_pp': 100*(ceiling-mean_recall),
        'checks': 'Per-customer scores match saved results; basket/miss partitions reconcile; no new-product recommendations.',
        'limits': 'Miss shares pool product lines and weight larger baskets more, unlike mean per-user recall. New means not in provided eligible history, not never bought in life. Perfect ranking uses hidden answers only to calculate an upper bound; not an implementable model or promised improvement.'
    }
    # Save customer diagnosis locally and the aggregate explanation in the check report.
    with duckdb.connect() as export:
        export.from_df(diagnostic).write_parquet(str(output/'validation_personal_miss_diagnosis.parquet'))
    (ROOT/'05_Results/03_Checks/validation_miss_diagnosis.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report, diagnostic


# Run this section only when the file is launched directly.
if __name__=='__main__':
    report, _ = classify_misses()
    print(json.dumps(report,indent=2))
