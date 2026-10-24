"""Compare saved weighted-recency and frequency validation scores by history length."""
from pathlib import Path
import json
import math
import sqlite3
from collections import Counter

# Find the project files and keep the same groups used in the earlier comparison.
ROOT = Path(__file__).resolve().parents[2]
GROUPS = [('Short: 1-5 orders', 1, 5), ('Medium: 6-15 orders', 6, 15),
          ('Long: 16+ orders', 16, None)]
METRICS = ['precision_at_5', 'recall_at_5', 'hit_at_5']


def compare_recency_groups():
    import duckdb  # Historical route; the current tree comparison below uses SQLite only.
    # Read existing scores; don't retrain anything or open the final baskets.
    outputs = ROOT / '02_Data/03_Model_Outputs'
    with duckdb.connect(str(ROOT / '02_Data/02_Prepared/instacart.duckdb'), read_only=True) as con:
        frequency = con.read_parquet(str(outputs / 'validation_personal_frequency_scores.parquet')).df()
        recency = con.read_parquet(str(outputs / 'validation_weighted_recency_scores.parquet')).df()
        paired = frequency.merge(recency,
            on=['user_id', 'validation_order_id', 'actual_products'],
            suffixes=('_frequency', '_recency'), validate='one_to_one')
        assert len(paired) == len(frequency) == len(recency)
        # History size counts only orders before each customer's validation basket.
        history = con.execute('''SELECT e.user_id, COUNT(*) AS history_orders
            FROM evaluation_plan e JOIN orders o ON e.user_id=o.user_id
            WHERE o.eval_set='prior' AND o.order_number<=e.validation_history_max_order_number
            GROUP BY e.user_id''').df()
        paired = paired.merge(history, on='user_id', validate='one_to_one')
        assert len(paired) == len(frequency)
        assert paired.history_orders.ge(1).all()

    # Summarise the same customers under both methods within each history group.
    summaries = []
    assigned = set()
    for name, low, high in GROUPS:
        mask = paired.history_orders.ge(low)
        if high is not None:
            mask &= paired.history_orders.le(high)
        group = paired.loc[mask]
        assert len(group) > 1
        ids = set(group.user_id)
        assert not assigned.intersection(ids)
        assigned.update(ids)
        row = {'group': name, 'customers': len(group),
               'mean_basket_products': float(group.actual_products.mean())}
        for metric in METRICS:
            # Compare each customer with themselves, then average the differences.
            delta = group[f'{metric}_recency'] - group[f'{metric}_frequency']
            margin = 1.96 * delta.std(ddof=1) / math.sqrt(len(group))
            row[metric] = {
                'frequency': float(group[f'{metric}_frequency'].mean()),
                'recency': float(group[f'{metric}_recency'].mean()),
                'difference_pp': float(delta.mean() * 100),
                'paired_approx_95pct_interval_pp': [
                    float((delta.mean() - margin) * 100), float((delta.mean() + margin) * 100)]}
        # A group-average improvement doesn't mean every customer improved.
        change = group.matched_products_recency - group.matched_products_frequency
        row['customers_with_more_matches'] = int(change.gt(0).sum())
        row['customers_with_equal_matches'] = int(change.eq(0).sum())
        row['customers_with_fewer_matches'] = int(change.lt(0).sum())
        assert sum(row[k] for k in ['customers_with_more_matches',
            'customers_with_equal_matches', 'customers_with_fewer_matches']) == len(group)
        summaries.append(row)

    # Check that no customer was lost and group averages recover the overall scores.
    assert len(assigned) == len(paired)
    for metric in METRICS:
        for method in ['frequency', 'recency']:
            overall = sum(g['customers'] * g[metric][method] for g in summaries) / len(paired)
            assert math.isclose(overall, paired[f'{metric}_{method}'].mean())
    report = {'stage': 'validation subgroup comparison; final evaluation not run',
        'customers': len(paired), 'history_definition': 'eligible past order count before validation',
        'groups': summaries,
        'checks': 'Same customers and baskets; all users assigned once; group averages reconcile.',
        'limits': 'Exploratory groups, not randomised effects of history length. Approximate intervals assume independent users. Higher group averages can coexist with individual losses; no causal shopping benefit established.'}
    (ROOT / '05_Results/03_Checks/recency_group_validation.json').write_text(
        json.dumps(report, indent=2), encoding='utf-8')
    return report


def compare_tree_tradeoffs():
    """Compare saved tree outcomes with the same fixed weighted-recency recipe."""
    # Read only checked validation inputs and saved results; don't fit or read final baskets.
    checks = ROOT/'05_Results/03_Checks'
    outputs = ROOT/'02_Data/03_Model_Outputs'
    tree_report = json.loads((checks/'boosted_trees_validation.json').read_text(encoding='utf-8'))
    assert tree_report['status']=='passed'
    with sqlite3.connect((outputs/'boosted_trees_validation.sqlite').as_uri()+'?mode=ro',uri=True) as saved:
        tree = {r[0]:r[1:] for r in saved.execute('''SELECT user_id,validation_order_id,
            actual_products,matched_products,history_orders FROM scores''')}
    with sqlite3.connect((ROOT/'02_Data/02_Prepared/instacart_ml.sqlite').as_uri()+'?mode=ro',uri=True) as con:
        assert con.execute("SELECT value FROM build_metadata WHERE key='features_checked'").fetchone()==('passed',)
        # Rank by purchase-history score only. Answers are summed only after choosing five.
        rows = con.execute('''WITH ranked AS (
            SELECT user_id,product_id,bought_next,
                ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY recency_score DESC,
                    last_purchase_order DESC,product_id) AS rank
            FROM ml_features WHERE stage='validation'
        ), matches AS (SELECT user_id,SUM(bought_next) AS hits FROM ranked WHERE rank<=5 GROUP BY user_id),
        sizes AS (SELECT e.user_id,COUNT(*) AS basket_size FROM evaluation_plan e
            JOIN order_products__prior i ON i.order_id=e.validation_order_id GROUP BY e.user_id)
        SELECT e.user_id,e.validation_order_id,s.basket_size,m.hits,e.validation_history_max_order_number
        FROM evaluation_plan e JOIN matches m USING(user_id) JOIN sizes s USING(user_id)
        ORDER BY e.user_id''').fetchall()
    assert len(rows)==len(tree)==tree_report['customers']==131209
    assert {r[0] for r in rows}==set(tree)
    overall = Counter()
    group_counts = {label:Counter() for label,_,_ in GROUPS}
    tree_metrics,recency_metrics = [],[]
    match_delta = Counter()
    # Pair each customer's results on exactly the same target and complete basket size.
    for uid,target,size,hits,history in rows:
        t_target,t_size,t_hits,t_history = tree[uid]
        assert (target,size,history)==(t_target,t_size,t_history)
        delta = t_hits-hits
        outcome = 'more_matches' if delta>0 else 'fewer_matches' if delta<0 else 'same_matches'
        overall[outcome]+=1
        match_delta[delta]+=1
        for label,low,high in GROUPS:
            if low<=history and (high is None or history<=high):
                group_counts[label][outcome]+=1
        tree_metrics.append((t_hits/5,t_hits/size,int(t_hits>0)))
        recency_metrics.append((hits/5,hits/size,int(hits>0)))
    # Reconcile individual results with all three saved aggregate metrics and group sizes.
    n = len(rows)
    for col,metric in enumerate(METRICS):
        assert math.isclose(sum(v[col] for v in tree_metrics)/n,
            tree_report['comparison'][metric]['boosted_trees'],abs_tol=1e-10)
        assert math.isclose(sum(v[col] for v in recency_metrics)/n,
            tree_report['comparison'][metric]['weighted_recency'],abs_tol=1e-10)
    assert sum(overall.values())==n
    assert sum(sum(v.values()) for v in group_counts.values())==n
    pooled_precision_change = sum(delta*count for delta,count in match_delta.items())/n/5
    mean_precision_change = sum(v[0]-u[0] for v,u in zip(tree_metrics,recency_metrics))/n
    assert math.isclose(pooled_precision_change,mean_precision_change,abs_tol=1e-12)
    def summary(counts):
        denominator = sum(counts.values())
        return {'customers':denominator,**{key:{'customers':counts[key],
            'pct_of_group':100*counts[key]/denominator} for key in
            ('more_matches','same_matches','fewer_matches')}}
    report = {'status':'passed','stage':'validation only; no model refit or final baskets',
        'comparison':'Boosted trees minus weighted recency; each customer paired on the same basket',
        'denominator':'All 131209 validation customers, one outcome per customer',
        'overall':summary(overall),'groups':{k:summary(v) for k,v in group_counts.items()},
        'matched_product_change_distribution':dict(sorted(match_delta.items())),
        'checks':{'same_cohort_targets_sizes_history':True,'group_counts_reconcile':True,
            'saved_tree_and_recency_metrics_reconcile':True},
        'limits':'Same match count does not imply the same suggested products. More matches are prediction gains, not proof of customer benefit. No runtime or maintenance superiority has been measured.'}
    (checks/'tree_customer_tradeoffs.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report


def compare_basket_sizes():
    """Compare saved methods by actual target basket size, for diagnosis only."""
    checks = ROOT/'05_Results/03_Checks'
    outputs = ROOT/'02_Data/03_Model_Outputs'
    # Fix bins before inspecting results. Actual basket size is never a prediction input.
    bins = [('1-5 products',1,5),('6-10 products',6,10),
            ('11-20 products',11,20),('21+ products',21,None)]
    scored = {}
    for method,prefix in [('logistic_regression','logistic'),('boosted_trees','boosted_trees')]:
        with sqlite3.connect((outputs/f'{prefix}_validation.sqlite').as_uri()+'?mode=ro',uri=True) as saved:
            scored[method] = {r[0]:r[1:] for r in saved.execute('''SELECT user_id,
                validation_order_id,actual_products,matched_products FROM scores''')}
    # Rebuild only fixed weighted-recency ranking, and count full actual validation baskets.
    with sqlite3.connect((ROOT/'02_Data/02_Prepared/instacart_ml.sqlite').as_uri()+'?mode=ro',uri=True) as con:
        assert con.execute("SELECT value FROM build_metadata WHERE key='features_checked'").fetchone()==('passed',)
        rows = con.execute('''WITH ranked AS (SELECT user_id,bought_next,ROW_NUMBER() OVER (
                PARTITION BY user_id ORDER BY recency_score DESC,last_purchase_order DESC,product_id) AS rank
                FROM ml_features WHERE stage='validation'),
            hits AS (SELECT user_id,SUM(bought_next) AS matched FROM ranked WHERE rank<=5 GROUP BY user_id),
            sizes AS (SELECT e.user_id,COUNT(*) AS actual_size FROM evaluation_plan e
                JOIN order_products__prior i ON i.order_id=e.validation_order_id GROUP BY e.user_id)
            SELECT e.user_id,e.validation_order_id,s.actual_size,h.matched
            FROM evaluation_plan e JOIN hits h USING(user_id) JOIN sizes s USING(user_id)
            ORDER BY e.user_id''').fetchall()
    scored['weighted_recency'] = {r[0]:r[1:] for r in rows}
    ids = set(scored['weighted_recency'])
    assert len(ids)==131209 and all(set(v)==ids for v in scored.values())
    for uid in ids:
        expected = scored['weighted_recency'][uid][:2]
        assert expected[1]>0
        for values in scored.values():
            assert values[uid][:2]==expected
            assert 0<=values[uid][2]<=min(5,expected[1])
    methods = ['weighted_recency','logistic_regression','boosted_trees']
    expected_reports = {
        method:json.loads((checks/f'{prefix}_validation.json').read_text(encoding='utf-8'))
        for method,prefix in [('logistic_regression','logistic'),('boosted_trees','boosted_trees')]}
    recency_report = json.loads((checks/'weighted_recency_validation.json').read_text(encoding='utf-8'))
    summaries,assigned = [],set()
    for label,low,high in bins:
        users = sorted(uid for uid in ids if low<=scored['weighted_recency'][uid][1]
                       and (high is None or scored['weighted_recency'][uid][1]<=high))
        assert users and not (assigned & set(users))
        assigned.update(users)
        sizes = [scored['weighted_recency'][uid][1] for uid in users]
        result = {'actual_basket_size':label,'customers':len(users),
            'mean_basket_products':sum(sizes)/len(users),
            'mean_five_slot_recall_ceiling':sum(min(5,size)/size for size in sizes)/len(users),
            'methods':{}}
        for method in methods:
            hits = [scored[method][uid][2] for uid in users]
            result['methods'][method] = {
                'precision_at_5':sum(h/5 for h in hits)/len(users),
                'recall_at_5':sum(h/s for h,s in zip(hits,sizes))/len(users),
                'hit_at_5':sum(h>0 for h in hits)/len(users)}
        differences = [(scored['boosted_trees'][uid][2]-scored['weighted_recency'][uid][2])/
                       scored['weighted_recency'][uid][1] for uid in users]
        result['tree_minus_recency_recall_pp'] = 100*sum(differences)/len(users)
        summaries.append(result)
    # Every user belongs to one group; group-weighted means must recover saved overall scores.
    assert assigned==ids and sum(row['customers'] for row in summaries)==len(ids)
    for method in methods:
        reference = recency_report['comparison'] if method=='weighted_recency' else expected_reports[method]['comparison']
        for metric in METRICS:
            actual = sum(row['customers']*row['methods'][method][metric] for row in summaries)/len(ids)
            expected = reference[metric][method]
            assert math.isclose(actual,expected,abs_tol=1e-10),(method,metric)
    report = {'status':'passed','stage':'validation diagnostics; no training or final baskets',
        'customers':len(ids),'group_rule':'Fixed actual basket sizes:1-5,6-10,11-20,21+ products',
        'groups':summaries,
        'denominators':{'precision':'matches / five, calculated per customer then averaged',
            'recall':'matches / all distinct actual basket products, calculated per customer then averaged',
            'hit_rate':'customers with at least one match / customers in that group'},
        'checks':{'same_users_targets_full_basket_sizes':True,'each_user_in_one_group':True,
            'all_saved_overall_metrics_reconcile':True},
        'limits':'Actual basket size is used after prediction for diagnosis, never as an input. '
            'Five slots structurally limit recall in larger baskets; lower recall alone does not establish worse ranking. '
            'The reported five-slot ceiling ignores familiar-product constraints and is not an achievable model promise. '
            'Exploratory groups, not causal effects or proof of customer benefit.'}
    (checks/'basket_size_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report


def compare_product_coverage():
    """Audit recommendation breadth, concentration and short lists on matching users."""
    import csv
    checks = ROOT/'05_Results/03_Checks'
    outputs = ROOT/'02_Data/03_Model_Outputs'
    methods = ['weighted_recency','logistic_regression','boosted_trees']
    # Fix the concentration definition before viewing results: each method's ten most suggested products.
    top_k = 10
    with (ROOT/'02_Data/01_Original/products.csv').open(encoding='utf-8-sig',newline='') as handle:
        catalog = {int(row['product_id']):row['product_name'] for row in csv.DictReader(handle)}
    with sqlite3.connect((ROOT/'02_Data/02_Prepared/instacart_ml.sqlite').as_uri()+'?mode=ro',uri=True) as con:
        assert con.execute("SELECT value FROM build_metadata WHERE key='features_checked'").fetchone()==('passed',)
        cohort = dict(con.execute('SELECT user_id,validation_order_id FROM evaluation_plan'))
        candidate_counts = dict(con.execute("SELECT user_id,COUNT(*) FROM ml_features WHERE stage='validation' GROUP BY user_id"))
        assert set(candidate_counts)==set(cohort) and len(cohort)==131209
        eligible = {row[0] for row in con.execute("SELECT DISTINCT product_id FROM ml_features WHERE stage='validation'")}
        assert eligible<=set(catalog)
        # Temporary working tables are separate from the read-only prepared source database.
        con.execute('''CREATE TEMP TABLE coverage_recs(method TEXT,user_id INTEGER,
            product_id INTEGER,rank INTEGER,PRIMARY KEY(method,user_id,rank),
            UNIQUE(method,user_id,product_id))''')
        con.execute('''INSERT INTO coverage_recs
            WITH ranked AS (SELECT user_id,product_id,ROW_NUMBER() OVER (
                PARTITION BY user_id ORDER BY recency_score DESC,last_purchase_order DESC,product_id) AS rank
                FROM ml_features WHERE stage='validation')
            SELECT 'weighted_recency',user_id,product_id,rank FROM ranked WHERE rank<=5''')
        # Reuse saved ML recommendations, rather than score models again.
        for method,prefix in [('logistic_regression','logistic'),('boosted_trees','boosted_trees')]:
            saved_report = json.loads((checks/f'{prefix}_validation.json').read_text(encoding='utf-8'))
            assert saved_report['status']=='passed'
            con.execute(f'ATTACH DATABASE ? AS {prefix}',[(outputs/f'{prefix}_validation.sqlite').as_uri()+'?mode=ro'])
            saved_cohort = dict(con.execute(f'SELECT user_id,validation_order_id FROM {prefix}.scores'))
            assert saved_cohort==cohort
            con.execute(f'INSERT INTO coverage_recs SELECT ?,user_id,product_id,rank FROM {prefix}.recommendations',[method])
        # Every list must contain min(5, eligible familiar products), without ineligible suggestions.
        assert con.execute('''SELECT COUNT(*) FROM coverage_recs r LEFT JOIN ml_features f
            ON f.stage='validation' AND f.user_id=r.user_id AND f.product_id=r.product_id
            WHERE f.product_id IS NULL OR r.rank NOT BETWEEN 1 AND 5''').fetchone()[0]==0
        expected_slots = sum(min(5,n) for n in candidate_counts.values())
        expected_short = sum(n<5 for n in candidate_counts.values())
        summaries = {}
        for method in methods:
            lengths = dict(con.execute('SELECT user_id,COUNT(*) FROM coverage_recs WHERE method=? GROUP BY user_id',[method]))
            assert set(lengths)==set(cohort)
            assert all(lengths[uid]==min(5,candidate_counts[uid]) for uid in cohort)
            counts = con.execute('''SELECT product_id,COUNT(*) AS slots FROM coverage_recs
                WHERE method=? GROUP BY product_id ORDER BY slots DESC,product_id''',[method]).fetchall()
            total = sum(n for _,n in counts)
            assert total==expected_slots and {pid for pid,_ in counts}<=eligible
            leaders = counts[:top_k]
            summaries[method] = {
                'customers':len(lengths),'suggestion_slots':total,
                'distinct_products_suggested':len(counts),
                'pct_of_eligible_product_pool_suggested':100*len(counts)/len(eligible),
                'customers_with_fewer_than_five':sum(n<5 for n in lengths.values()),
                'short_list_pct_of_customers':100*expected_short/len(cohort),
                'filled_slot_pct_of_five_per_customer':100*total/(5*len(cohort)),
                'top10_share_of_suggestion_slots_pct':100*sum(n for _,n in leaders)/total,
                'top10_products':[{'product_id':pid,'product_name':catalog[pid],'suggestion_slots':n,
                    'share_of_suggestion_slots_pct':100*n/total} for pid,n in leaders]}
            assert summaries[method]['customers_with_fewer_than_five']==expected_short==3521
        report = {'status':'passed','stage':'validation only; saved results and fixed ranking, no training',
            'customers':len(cohort),'source_catalog_products':len(catalog),
            'eligible_product_pool':len(eligible),
            'definitions':{
                'eligible_pool':'Distinct products across personal candidates in validation history; not the full catalog or next-basket answers.',
                'coverage':'Distinct suggested products / eligible product pool, counted across the cohort.',
                'concentration':'Share of all filled suggestion slots occupied by each method\'s own ten most suggested products; top10 fixed before inspection.',
                'short_lists':'Customers receiving fewer than five / all matching validation customers.',
                'slot_fill':'Total suggestions / (five times matching customers).'},
            'methods':summaries,
            'checks':{'same_users_and_targets':True,'unique_products_and_ranks':True,
                'all_suggestions_in_personal_eligible_history':True,
                'list_lengths_match_candidates':True,'slot_and_product_counts_reconcile':True},
            'limits':'Cohort-level breadth, not new-product discovery or diversity inside one basket. More distinct products is not automatically better for Buy again. No impressions, stock, conversion effect or customer benefit measured; final baskets untouched.'}
    (checks/'product_coverage_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report


def benchmark_prediction_speed():
    """Time matched, warmed per-customer work; no training or final evaluation."""
    import hashlib
    import platform
    import random
    import tempfile
    import time
    import joblib
    import numpy as np
    import sklearn
    from scipy.special import expit
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import make_pipeline
    from threadpoolctl import threadpool_limits

    checks = ROOT/'05_Results/03_Checks'
    outputs = ROOT/'02_Data/03_Model_Outputs'
    features = ['purchase_orders','purchase_share','orders_since_last_purchase','recency_score','history_orders']
    # Fix the sample and repetitions before timing; don't choose customers based on measured speed.
    repeats,per_group,warmups,seed = 20,30,3,20261022
    spec = {'status':'started','customers_per_history_group':per_group,'repetitions':repeats,
        'warmups':warmups,'seed':seed,'thread_limit':2,
        'sampling':'30 customers per fixed history group, lowest SHA256(seed:user_id), independent of outcomes',
        'timing_scope':'Prepared feature fetch/format, scoring+ranking, cached-list fetch: separate warm local stages',
        'excluded':'Raw-history feature generation, model loading/training, cold-start, browser, network and app rendering',
        'final_baskets_scored':False}
    report_path = checks/'prediction_runtime.json'
    report_path.write_text(json.dumps(spec,indent=2),encoding='utf-8')
    # Load the trusted local tree once, outside measured calls, as a running service would.
    model = joblib.load(outputs/'boosted_trees_model.joblib')
    # Restore the original fitted logistic scaler/weights, without learning anything again.
    state = json.loads((outputs/'logistic_model.json').read_text(encoding='utf-8'))
    logistic_report = json.loads((checks/'logistic_validation.json').read_text(encoding='utf-8'))
    assert state['features']==features and logistic_report['status']=='passed'
    assert state['sklearn_version']==sklearn.__version__
    scaler = StandardScaler()
    scaler.mean_ = np.asarray(state['mean'],dtype=np.float64)
    scaler.scale_ = np.asarray(state['scale'],dtype=np.float64)
    scaler.var_ = scaler.scale_**2
    scaler.n_features_in_ = len(features)
    scaler.n_samples_seen_ = logistic_report['training_rows']
    classifier = LogisticRegression(**state['settings'])
    classifier.coef_ = np.asarray([state['coefficients']],dtype=np.float64)
    classifier.intercept_ = np.asarray([state['intercept']],dtype=np.float64)
    classifier.classes_ = np.asarray([0,1])
    classifier.n_features_in_ = len(features)
    classifier.n_iter_ = np.asarray([logistic_report['iterations']])
    logistic = make_pipeline(scaler,classifier)
    rng = random.Random(seed)
    methods = ['weighted_recency','logistic_regression','boosted_trees']
    spec['methods'] = methods
    spec['logistic_note'] = 'Restored saved original weights/scaler with the original library version; timed library scaling+prediction+ranking, no refit.'
    results = {label:[] for label,_,_ in GROUPS}
    predictions = {}
    query = ('SELECT product_id,last_purchase_order,'+','.join(features)+
             " FROM ml_features WHERE stage='validation' AND user_id=? ORDER BY product_id")

    def fetch_features(con,uid):
        rows = con.execute(query,[uid]).fetchall()
        matrix = np.asarray(rows,dtype=np.float64)
        return matrix[:,0].astype(np.int64),matrix[:,1].astype(np.int64),np.ascontiguousarray(matrix[:,2:])

    def predict(method,data):
        ids,last,x = data
        if method=='weighted_recency':
            scores = x[:,3]
        elif method=='logistic_regression':
            scores = logistic.predict_proba(x)[:,1]
        else:
            scores = model.predict_proba(x)[:,1]
        # All methods rank exactly the same products with exactly the same tie-breaks.
        order = np.lexsort((ids,-last,-scores))[:5]
        return list(zip(ids[order].tolist(),scores[order].tolist()))

    def stats(values):
        return {'observations':len(values),'median_ms':float(np.median(values)),
                'p95_ms':float(np.percentile(values,95))}

    with sqlite3.connect((ROOT/'02_Data/02_Prepared/instacart_ml.sqlite').as_uri()+'?mode=ro',uri=True) as con, threadpool_limits(limits=2):
        assert con.execute("SELECT value FROM build_metadata WHERE key='features_checked'").fetchone()==('passed',)
        all_users = con.execute('SELECT user_id,validation_history_max_order_number FROM evaluation_plan').fetchall()
        selected = []
        for label,low,high in GROUPS:
            pool = [uid for uid,h in all_users if low<=h and (high is None or h<=high)]
            chosen = sorted(pool,key=lambda uid:hashlib.sha256(f'{seed}:{uid}'.encode()).digest())[:per_group]
            assert len(chosen)==per_group
            selected.extend((uid,label) for uid in chosen)
        assert len({uid for uid,_ in selected})==90
        rng.shuffle(selected)
        # Sample size and candidate counts are audit details; detailed user IDs stay local in cache only.
        for uid,label in selected:
            data = fetch_features(con,uid)
            assert len(data[0])>0 and len(set(data[0]))==len(data[0])
            # Confirm the restored library pipeline matches the saved logistic equation.
            x = data[2]
            portable = expit(((x-scaler.mean_)/scaler.scale_) @ classifier.coef_[0]+classifier.intercept_[0])
            assert np.allclose(portable,logistic.predict_proba(x)[:,1],atol=1e-12)
            expected = {method:predict(method,data) for method in methods}
            for method in methods:
                predictions[uid,method] = expected[method]
            for _ in range(warmups):
                fetch_features(con,uid)
                for method in methods:
                    predict(method,data)
            feature_ms,calculation = [],{method:[] for method in methods}
            for _ in range(repeats):
                started = time.perf_counter_ns()
                fresh = fetch_features(con,uid)
                feature_ms.append((time.perf_counter_ns()-started)/1e6)
                assert np.array_equal(fresh[0],data[0]) and np.array_equal(fresh[2],data[2])
                order = methods.copy()
                rng.shuffle(order)
                for method in order:
                    started = time.perf_counter_ns()
                    chosen = predict(method,data)
                    calculation[method].append((time.perf_counter_ns()-started)/1e6)
                    assert chosen==expected[method]
            results[label].append({'candidates':len(data[0]),'feature_ms':feature_ms,'calculation':calculation})
        # Verify sampled tree rankings match the actual saved validation lists, outside timers.
        with sqlite3.connect((outputs/'boosted_trees_validation.sqlite').as_uri()+'?mode=ro',uri=True) as saved:
            for uid,_ in selected:
                actual = [row[0] for row in saved.execute('SELECT product_id FROM recommendations WHERE user_id=? ORDER BY rank',[uid])]
                assert actual==[pid for pid,_ in predictions[uid,'boosted_trees']]
        with sqlite3.connect((outputs/'logistic_validation.sqlite').as_uri()+'?mode=ro',uri=True) as saved:
            for uid,_ in selected:
                actual = [row[0] for row in saved.execute('SELECT product_id FROM recommendations WHERE user_id=? ORDER BY rank',[uid])]
                assert actual==[pid for pid,_ in predictions[uid,'logistic_regression']]

    # Put all three methods' precomputed lists in the same temporary disk cache.
    cached = {method:[] for method in methods}
    with tempfile.TemporaryDirectory(prefix='runtime_cache_',dir=outputs) as folder:
        with sqlite3.connect(str(Path(folder)/'lists.sqlite')) as cache:
            cache.execute('''CREATE TABLE lists(method TEXT,user_id INTEGER,rank INTEGER,
                product_id INTEGER,score REAL,PRIMARY KEY(method,user_id,rank)) WITHOUT ROWID''')
            cache.executemany('INSERT INTO lists VALUES (?,?,?,?,?)',[
                (method,uid,rank,pid,score) for (uid,method),recs in predictions.items()
                for rank,(pid,score) in enumerate(recs,1)])
            cache.commit()
            fetch_sql = 'SELECT product_id,score FROM lists WHERE method=? AND user_id=? ORDER BY rank'
            for uid,_ in selected:
                for method in methods:
                    for _ in range(warmups):
                        cache.execute(fetch_sql,[method,uid]).fetchall()
                for _ in range(repeats):
                    order = methods.copy()
                    rng.shuffle(order)
                    for method in order:
                        started = time.perf_counter_ns()
                        values = cache.execute(fetch_sql,[method,uid]).fetchall()
                        cached[method].append((time.perf_counter_ns()-started)/1e6)
                        assert values==predictions[uid,method]
        # TemporaryDirectory removes only this task-created cache after closing its connection.
        cache.close()

    rows = [row for group in results.values() for row in group]
    spec.update({'status':'passed','customers':len(rows),'model_refitted':False,
        'feature_fetch_and_format':stats([v for row in rows for v in row['feature_ms']]),
        'scoring_and_ranking':{method:stats([v for row in rows for v in row['calculation'][method]]) for method in methods},
        'cached_list_retrieval':{method:stats(cached[method]) for method in methods},
        'history_groups':{label:{'customers':len(group),
            'candidate_count_min':min(row['candidates'] for row in group),
            'candidate_count_median':float(np.median([row['candidates'] for row in group])),
            'candidate_count_max':max(row['candidates'] for row in group),
            'scoring_and_ranking':{method:stats([v for row in group for v in row['calculation'][method]]) for method in methods}}
            for label,group in results.items()},
        'environment':{'python':platform.python_version(),'sqlite':sqlite3.sqlite_version,
            'scikit_learn':sklearn.__version__,'platform':platform.system()},
        'checks':{'same_candidates_and_ties':True,'predictions_stable_across_repeats':True,
            'sampled_tree_lists_match_saved_results':True,'cached_lists_match_inference':True,
            'restored_logistic_matches_saved_equation':True,'sampled_logistic_lists_match_saved_results':True,
            'randomised_calculation_order':True,'all_ninety_users_assigned_once':True},
        'limits':'Warm local microbenchmark with 30 customers per history group, not population-weighted or concurrent load testing. '
            'Cached retrieval uses a small temporary SQLite database, not a production-size cache. '
            'Repeated calls are not independent user samples. Results exclude feature construction, network and rendering; not end-to-end app latency.'})
    report_path.write_text(json.dumps(spec,indent=2),encoding='utf-8')
    return spec


# Run a selected comparison without importing the blocked engine for the SQLite route.
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--trees',action='store_true',help='SQLite: compare tree vs recency customer outcomes')
    mode.add_argument('--benchmark',action='store_true',help='Warm local matched prediction and cached-retrieval benchmark')
    mode.add_argument('--coverage',action='store_true',help='Compare all three personal methods on product coverage and concentration')
    mode.add_argument('--basket-size',action='store_true',help='Compare all three methods by actual validation basket size')
    args = parser.parse_args()
    if args.basket_size:
        result = compare_basket_sizes()
    elif args.coverage:
        result = compare_product_coverage()
    elif args.benchmark:
        result = benchmark_prediction_speed()
    elif args.trees:
        result = compare_tree_tradeoffs()
    else:
        result = compare_recency_groups()
    print(json.dumps(result,indent=2))
