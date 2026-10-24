"""Build a validation popularity list without scoring the hidden baskets."""
# Load the Python tools used by this script.
from pathlib import Path
import json
import duckdb

# Find the project folder so paths work from different starting locations.
ROOT = Path(__file__).resolve().parents[2]


# Build the same five-product list for all evaluation customers.
def build_baseline():
    # Read the SQL recipe and open the prepared database read-only.
    query = (ROOT / '03_Code/02_Baselines/popularity_baseline.sql').read_text(encoding='utf-8')
    with duckdb.connect(str(ROOT / '02_Data/02_Prepared/instacart.duckdb'), read_only=True) as con:
        # Independently check that the eligible order set contains no held-out basket.
        checks = con.execute("""
            SELECT COUNT(*) AS history_orders,
                   COUNT(DISTINCT o.order_id) AS unique_history_orders,
                   COUNT(DISTINCT o.user_id) AS history_users,
                   COUNT(*) FILTER (WHERE o.order_id = e.validation_order_id
                                       OR o.order_id = e.final_target_order_id) AS target_overlap
            FROM orders o JOIN evaluation_plan e USING(user_id)
            WHERE o.eval_set = 'prior'
              AND o.order_number <= e.validation_history_max_order_number
        """).fetchone()
        assert checks[0] == checks[1] and checks[0] > 0
        assert checks[3] == 0, 'Held-out order found in history'
        expected_users = con.execute('SELECT COUNT(*) FROM evaluation_plan').fetchone()[0]
        assert checks[2] == expected_users
        # Run the ranking query and check the five products and denominator.
        frame = con.execute(query).df()
        assert len(frame) == 5 and frame.product_id.nunique() == 5
        assert frame.eligible_history_orders.eq(checks[0]).all()
        assert frame.orders_containing_product.is_monotonic_decreasing
        assert frame.orders_containing_product.between(1, checks[0]).all()
    # Collect the history counts and cutoff checks, without scoring any basket.
    report = {
        'stage': 'validation baseline built; no prediction accuracy scored',
        'cohort': 'evaluation_plan customers only; test-final customers excluded',
        'history_users': checks[2],
        'eligible_history_orders': checks[0],
        'held_out_order_overlap': checks[3],
        'denominator': 'eligible prior orders before each customer validation basket',
        'tie_break': 'ascending product_id',
        'recommendations': frame.to_dict(orient='records'),
        'limitation': 'Order sequences are per customer; this is not a shared calendar-date backtest.'
    }
    # Save the check report and return the list for display.
    (ROOT / '05_Results/03_Checks/popularity_baseline_validation.json').write_text(
        json.dumps(report, indent=2), encoding='utf-8'
    )
    return frame


# Run this section only when the file is launched directly.
if __name__ == '__main__':
    print(build_baseline().to_string(index=False))
