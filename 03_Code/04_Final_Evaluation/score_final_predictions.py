"""Score the already-frozen final lists once; never generate or modify predictions."""
import csv
import hashlib
import json
import math
from pathlib import Path
import sqlite3
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
METRICS = ['precision_at_5','recall_at_5','hit_at_5','mean_matches']


def frozen_evidence_path(relative):
    # Reports keep their original paths; archived code preserves the exact audited bytes.
    path = ROOT / relative
    if path.exists():
        return path
    archived = ROOT / '99_Archive/03_Frozen_Evaluation_Code' / relative
    if not archived.is_file():
        raise FileNotFoundError(f'Frozen evidence missing: {relative}')
    return archived



def fingerprint(path):
    value = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda:handle.read(1024*1024),b''):
            value.update(block)
    return value.hexdigest()


def score():
    checks = ROOT/'05_Results/03_Checks'
    output = ROOT/'02_Data/03_Model_Outputs'
    destination,working = output/'final_scores.sqlite',output/'final_scores.building.sqlite'
    if destination.exists() or working.exists():
        raise FileExistsError('A final scoring artifact exists. Review it; do not overwrite the exposed holdout run.')
    prediction_report_path = checks/'final_prediction_preparation.json'
    prep = json.loads(prediction_report_path.read_text(encoding='utf-8'))
    assert prep['status']=='passed' and prep['selected_default']=='weighted_recency'
    predictions = ROOT/prep['predictions_database']
    # Verify the exact frozen lists, original sources, models and documented plan BEFORE answers.
    assert fingerprint(predictions)==prep['predictions_sha256'],'Frozen prediction file changed'
    for group in ['source_sha256','model_sha256','code_and_plan_sha256']:
        for path,expected in prep[group].items():
            assert fingerprint(frozen_evidence_path(path))==expected,(group,path)
    answer_path = ROOT/'02_Data/01_Original/order_products__train.csv'
    manifest = json.loads((checks/'source_manifest.json').read_text(encoding='utf-8'))
    answer_hash = fingerprint(answer_path)
    assert answer_hash==manifest['files']['order_products__train.csv']['sha256']
    report_path = checks/'final_evaluation.json'
    report = {'status':'started','stage':'final evaluation; frozen predictions, no refit',
        'selected_default':'weighted_recency','prediction_sha256':prep['predictions_sha256'],
        'prediction_report_sha256':fingerprint(prediction_report_path),
        'scoring_code_sha256':fingerprint(Path(__file__).resolve()),
        'final_answer_source_sha256':answer_hash,'pre_answer_fingerprint_checks_passed':True,
        'models_refitted':False,'predictions_regenerated':False,
        'selection_changed_from_final_scores':False,'final_answers_opened_for_scoring':False}
    report_path.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('Frozen lists, sources, models and plan verified. Opening final answers for scoring.',flush=True)
    started = time.perf_counter()
    methods = prep['methods']
    with sqlite3.connect(working.as_uri(),uri=True) as con:
        con.execute('PRAGMA cache_size=-131072')
        con.execute('ATTACH DATABASE ? AS predictions',[predictions.as_uri()+'?mode=ro'])
        assert con.execute("SELECT value FROM predictions.build_metadata WHERE key='predictions_checked'").fetchone()==('passed',)
        targets = {r[0]:(r[1],r[2]) for r in con.execute('SELECT user_id,target_order_id,history_max_order FROM predictions.targets')}
        order_users = {v[0]:uid for uid,v in targets.items()}
        assert len(targets)==len(order_users)==131209
        samples = set(sorted(targets)[:100])
        raw_sample_answers = {uid:set() for uid in samples}
        con.execute('''CREATE TABLE answers(order_id INTEGER,product_id INTEGER,
            PRIMARY KEY(order_id,product_id)) WITHOUT ROWID''')
        # First semantic read of final product answers for evaluation. No scoring results change lists.
        report['final_answers_opened_for_scoring'] = True
        report_path.write_text(json.dumps(report,indent=2),encoding='utf-8')
        batch,answer_rows = [],0
        with answer_path.open(encoding='utf-8-sig',newline='') as handle:
            for row in csv.DictReader(handle):
                oid,pid = int(row['order_id']),int(row['product_id'])
                assert oid in order_users,'Unexpected final target'
                batch.append((oid,pid))
                answer_rows+=1
                uid = order_users[oid]
                if uid in samples:
                    raw_sample_answers[uid].add(pid)
                if len(batch)>=50_000:
                    con.executemany('INSERT INTO answers VALUES (?,?)',batch)
                    batch.clear()
        con.executemany('INSERT INTO answers VALUES (?,?)',batch)
        assert answer_rows==1_384_617
        con.execute('CREATE TABLE basket_sizes AS SELECT order_id,COUNT(*) AS actual_products FROM answers GROUP BY order_id')
        con.execute('CREATE UNIQUE INDEX final_answer_orders ON basket_sizes(order_id)')
        sizes = dict(con.execute('SELECT * FROM basket_sizes'))
        assert set(sizes)==set(order_users) and all(v>0 for v in sizes.values())
        # Join answers to fixed lists and measure overlap, never recalculate recommendation scores.
        print('Final answers checked. Calculating overlaps for the saved five methods...',flush=True)
        con.execute('''CREATE TABLE scores AS SELECT r.method,r.user_id,t.target_order_id,
            s.actual_products,COUNT(a.product_id) AS matched_products,COUNT(*) AS list_length,
            COUNT(a.product_id)/5.0 AS precision_at_5,
            COUNT(a.product_id)*1.0/s.actual_products AS recall_at_5,
            CAST(COUNT(a.product_id)>0 AS INTEGER) AS hit_at_5,
            t.history_max_order AS history_orders
            FROM predictions.recommendations r JOIN predictions.targets t ON t.user_id=r.user_id
            JOIN basket_sizes s ON s.order_id=t.target_order_id
            LEFT JOIN answers a ON a.order_id=t.target_order_id AND a.product_id=r.product_id
            GROUP BY r.method,r.user_id,t.target_order_id,s.actual_products,t.history_max_order''')
        con.execute('CREATE UNIQUE INDEX final_score_keys ON scores(method,user_id)')
        assert con.execute('''SELECT COUNT(*) FROM scores WHERE matched_products<0
            OR matched_products>5 OR matched_products>actual_products OR matched_products>list_length
            OR precision_at_5 NOT BETWEEN 0 AND 1 OR recall_at_5 NOT BETWEEN 0 AND 1
            OR hit_at_5 NOT IN (0,1) OR actual_products<=0''').fetchone()[0]==0
        ids = sorted(targets)
        arrays,overall = {},{}
        for method in methods:
            rows = con.execute('''SELECT user_id,target_order_id,actual_products,matched_products,
                precision_at_5,recall_at_5,hit_at_5,history_orders,list_length
                FROM scores WHERE method=? ORDER BY user_id''',[method]).fetchall()
            assert [r[0] for r in rows]==ids
            assert all((target,history)==targets[uid] and size==sizes[target]
                       for uid,target,size,hits,p,r,h,history,length in rows)
            arrays[method] = np.asarray([[row[4],row[5],row[6],row[3]] for row in rows],dtype=float)
            overall[method] = dict(zip(METRICS,arrays[method].mean(axis=0).tolist()))
            overall[method].update({'customers':len(rows),
                'matched_product_lines':sum(row[3] for row in rows),
                'suggestion_slots':sum(row[8] for row in rows),'short_lists':sum(row[8]<5 for row in rows)})
            assert overall[method]['suggestion_slots']==prep['methods_summary'][method]['suggestion_slots']
            assert overall[method]['short_lists']==prep['methods_summary'][method]['short_lists']
            # Independently calculate set intersections from the raw CSV answers for 100 fixed users.
            for row in rows[:100]:
                uid,target,size,hits,p,r,h,history,length = row
                recs = [r[0] for r in con.execute('SELECT product_id FROM predictions.recommendations WHERE method=? AND user_id=?',[method,uid])]
                expected = len(set(recs)&raw_sample_answers[uid])
                assert size==len(raw_sample_answers[uid]) and hits==expected
                assert math.isclose(p,expected/5) and math.isclose(r,expected/size) and h==int(expected>0)
        # Paired differences follow the prewritten plan. Positive means the first method did better.
        comparisons = {}
        for left,right in [('weighted_recency','personal_frequency'),('weighted_recency','popularity'),
                           ('logistic_regression','weighted_recency'),('boosted_trees','weighted_recency')]:
            delta = arrays[left]-arrays[right]
            details = {}
            for col,metric in enumerate(METRICS[:3]):
                diff = delta[:,col]
                margin = 1.96*diff.std(ddof=1)/math.sqrt(len(ids))
                details[metric] = {'difference_percentage_points':float(100*diff.mean()),
                    'paired_approx_95pct_interval_pp':[float(100*(diff.mean()-margin)),float(100*(diff.mean()+margin))]}
            comparisons[f'{left}_minus_{right}'] = {'metrics':details,
                'more_matches':int((delta[:,3]>0).sum()),'equal_matches':int((delta[:,3]==0).sum()),
                'fewer_matches':int((delta[:,3]<0).sum())}
        # Reuse fixed history and basket-size groups, with group-weighted reconciliation.
        history = np.asarray([targets[uid][1] for uid in ids])
        actual = np.asarray([sizes[targets[uid][0]] for uid in ids])
        group_reports = {}
        for dimension,values,bins in [
            ('history_orders',history,[('1-5',1,5),('6-15',6,15),('16+',16,None)]),
            ('actual_basket_products',actual,[('1-5',1,5),('6-10',6,10),('11-20',11,20),('21+',21,None)])]:
            groups,assigned = [],np.zeros(len(ids),dtype=int)
            for label,low,high in bins:
                mask = (values>=low)&(values<=high if high is not None else True)
                assert mask.any()
                assigned+=mask
                groups.append({'group':label,'customers':int(mask.sum()),'methods':{
                    method:dict(zip(METRICS,values_[mask].mean(axis=0).tolist())) for method,values_ in arrays.items()}})
            assert (assigned==1).all()
            for method in methods:
                for metric in METRICS:
                    rebuilt = sum(g['customers']*g['methods'][method][metric] for g in groups)/len(ids)
                    assert math.isclose(rebuilt,overall[method][metric],abs_tol=1e-10)
            group_reports[dimension]=groups
        # Coverage and concentration come from frozen lists, not a newly optimised ranking.
        pool = con.execute('SELECT COUNT(DISTINCT product_id) FROM predictions.final_features').fetchone()[0]
        coverage = {}
        for method in methods:
            counts = con.execute('''SELECT product_id,COUNT(*) AS n FROM predictions.recommendations
                WHERE method=? GROUP BY product_id ORDER BY n DESC,product_id''',[method]).fetchall()
            slots = sum(n for _,n in counts)
            assert slots==overall[method]['suggestion_slots']
            coverage[method]={'distinct_products':len(counts),'pct_of_eligible_pool':100*len(counts)/pool,
                'top10_share_of_slots_pct':100*sum(n for _,n in counts[:10])/slots,
                'short_lists':overall[method]['short_lists']}
        con.execute('CREATE TABLE build_metadata(key TEXT PRIMARY KEY,value TEXT)')
        con.executemany('INSERT INTO build_metadata VALUES (?,?)',[
            ('scoring_checked','passed'),('selected_default','weighted_recency'),
            ('frozen_predictions_sha256',prep['predictions_sha256'])])
        con.commit()
    con.close()
    # Frozen prediction bytes and original model/code/plan files must be unchanged after scoring.
    assert fingerprint(predictions)==prep['predictions_sha256']
    for group in ['source_sha256','model_sha256','code_and_plan_sha256']:
        assert all(fingerprint(frozen_evidence_path(path))==expected for path,expected in prep[group].items())
    working.rename(destination)
    report.update({'status':'passed','final_answers_opened_for_scoring':True,'customers':len(ids),
        'actual_product_lines':answer_rows,'overall':overall,'paired_comparisons':comparisons,
        'groups':group_reports,'eligible_product_pool':pool,'coverage':coverage,
        'score_database':str(destination.relative_to(ROOT)),'score_database_sha256':fingerprint(destination),
        'seconds':round(time.perf_counter()-started,2),
        'checks':{'frozen_artifacts_verified_before_and_after':True,'unique_complete_final_answers':True,
            'same_users_targets_sizes':True,'independent_overlap_users_per_method':100,
            'group_and_slot_totals_reconcile':True,'scores_in_valid_bounds':True},
        'metric_definitions':{'recall':'mean of each customer matches / all actual basket products',
            'precision':'mean matches / five, including unfilled slots','hit_rate':'customers with at least one match / all evaluated customers'},
        'limits':'This holdout is now inspected and must not be reused for tuning. Frozen original ML models, no refit. '
            'Paired approximate intervals assume independent customer identifiers. Groups are exploratory. '
            'Known-user order-sequence evaluation, not calendar-time simulation or causal/live benefit. '
            'Source sample is biased; no prices, quantities or exposures. Popularity can choose unfamiliar products.'})
    report_path.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('Final scoring checks passed. Frozen lists/models unchanged; selected method unchanged.',flush=True)
    print(json.dumps(overall,indent=2))


if __name__=='__main__':
    score()
