"""One prespecified five-order half-life experiment, evaluated on validation only."""
# Load the Python tools used by this script.
from pathlib import Path
from collections import defaultdict
import json
import math
import duckdb

# Find the project folder so paths work from different starting locations.
ROOT=Path(__file__).resolve().parents[2]


# Test the fixed five-order half-life rule on validation baskets only.
def run_experiment():
    # Locate local outputs and read the SQL weighting recipe.
    output=ROOT/'02_Data/03_Model_Outputs'
    sql=(ROOT/'03_Code/02_Baselines/weighted_recency.sql').read_text(encoding='utf-8')
    with duckdb.connect(str(ROOT/'02_Data/02_Prepared/instacart.duckdb'),read_only=True) as con:
        # Build up to five familiar-product suggestions per customer and check the lists.
        recs=con.execute(sql).df()
        assert not recs.duplicated(['user_id','product_id']).any()
        assert recs.recommendation_rank.between(1,5).all()
        assert recs.recency_score.gt(0).all()
        con.register('recency_recommendations',recs)
        # Measure overlap with hidden baskets using the same metrics as before.
        scores=con.execute('''SELECT e.user_id,e.validation_order_id,
            COUNT(DISTINCT i.product_id) AS actual_products,
            COUNT(DISTINCT CASE WHEN r.product_id IS NOT NULL THEN i.product_id END) AS matched_products,
            matched_products/5.0 AS precision_at_5,
            matched_products*1.0/actual_products AS recall_at_5,
            CAST(matched_products>0 AS INTEGER) AS hit_at_5
            FROM evaluation_plan e JOIN order_products__prior i ON i.order_id=e.validation_order_id
            LEFT JOIN recency_recommendations r ON r.user_id=e.user_id AND r.product_id=i.product_id
            GROUP BY e.user_id,e.validation_order_id ORDER BY e.user_id''').df()
        # Compare only when customer IDs, validation orders and basket sizes match.
        frequency=con.read_parquet(str(output/'validation_personal_frequency_scores.parquet')).df().sort_values('user_id').reset_index(drop=True)
        for col in ['user_id','validation_order_id','actual_products']:
            assert scores[col].equals(frequency[col]),col
        assert scores.actual_products.gt(0).all()
        assert scores.matched_products.between(0,5).all()
        assert scores.matched_products.le(scores.actual_products).all()
        for metric in ['precision_at_5','recall_at_5','hit_at_5']:
            assert scores[metric].between(0,1).all()
        # Independently rebuild the weighted rankings for 100 fixed customers.
        con.register('sample_users',scores.head(100)[['user_id']])
        raw=con.execute('''SELECT o.user_id,i.product_id,o.order_number,e.validation_history_max_order_number
            FROM orders o JOIN evaluation_plan e USING(user_id) JOIN sample_users s USING(user_id)
            JOIN order_products__prior i USING(order_id)
            WHERE o.eval_set='prior' AND o.order_number<=e.validation_history_max_order_number''').fetchall()
        # Give recent purchases more points and track the last purchase for tie-breaking.
        weights,latest=defaultdict(float),defaultdict(int)
        for uid,pid,number,cutoff in raw:
            weights[uid,pid]+=0.5**((cutoff-number)/5)
            latest[uid,pid]=max(latest[uid,pid],number)
        candidates=defaultdict(list)
        for uid,pid in weights:candidates[uid].append(pid)
        actual_recs=recs.groupby('user_id').product_id.apply(list).to_dict()
        for uid,pids in candidates.items():
            expected=sorted(pids,key=lambda pid:(-round(weights[uid,pid],12),-latest[uid,pid],pid))[:5]
            assert actual_recs[uid]==expected,uid
        # Verify cutoff safety and that both methods have the same filled slot counts.
        check=recs.merge(con.execute('SELECT user_id,validation_history_max_order_number FROM evaluation_plan').df(),on='user_id',validate='many_to_one')
        assert check.last_purchase_order_number.le(check.validation_history_max_order_number).all()
        freq_recs=con.read_parquet(str(output/'validation_personal_frequency_recommendations.parquet')).df()
        assert recs.groupby('user_id').size().equals(freq_recs.groupby('user_id').size())

    # Compare paired customer scores and calculate approximate uncertainty intervals.
    results={}
    for metric in ['precision_at_5','recall_at_5','hit_at_5']:
        diff=scores[metric]-frequency[metric]
        margin=1.96*diff.std(ddof=1)/math.sqrt(len(diff))
        results[metric]={'personal_frequency':float(frequency[metric].mean()),
            'weighted_recency':float(scores[metric].mean()),
            'difference_percentage_points':float(diff.mean()*100),
            'paired_approx_95pct_interval_pp':[float((diff.mean()-margin)*100),float((diff.mean()+margin)*100)]}
    # Record the fixed rule, scores and limits without selecting a final winner.
    report={'stage':'validation only; final baskets untouched',
        'rule':'Weight = 0.5 ** (age in order positions / 5), summed per product; round score to 12 decimal places before ranking.',
        'parameter_choice':'Five-order half-life fixed before seeing this experiment scores; no sweep or tuning performed.',
        'customers':len(scores),'comparison':results,
        'customers_with_fewer_than_five_suggestions':int((recs.groupby('user_id').size()<5).sum()),
        'checks':{'same_customers_targets_basket_sizes':True,'same_candidate_list_lengths':True,'independent_rankings_checked':100,'candidate_cutoffs_passed':True},
        'example_user_1':recs.loc[recs.user_id.eq(1)].to_dict(orient='records'),
        'limits':'Rebuy-only, like the frequency comparison. Order age is not elapsed days. Approximate intervals assume independent users; neither validation scores nor intervals establish causal benefit. No final method selected.'}
    # Save detailed validation outputs locally and the aggregate report separately.
    with duckdb.connect() as export:
        export.from_df(scores).write_parquet(str(output/'validation_weighted_recency_scores.parquet'))
        export.from_df(recs).write_parquet(str(output/'validation_weighted_recency_recommendations.parquet'))
    (ROOT/'05_Results/03_Checks/weighted_recency_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report,scores,recs


# Run this section only when the file is launched directly.
if __name__=='__main__':
    report,_,_=run_experiment()
    print(json.dumps(report,indent=2))
