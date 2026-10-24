"""Freeze final prediction lists BEFORE any final product answers are opened.

This script reads only prior products, order metadata and the original frozen models.
It deliberately has no final-answer file/table access or scoring function.
"""
import csv
import hashlib
import heapq
import json
import math
from pathlib import Path
import pickle
import sqlite3
import time

import joblib
import numpy as np
import pandas as pd
from scipy.special import expit
from threadpoolctl import threadpool_limits
# Reuse the checked model loader from the comparison stage.
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '03_Model_Comparison'))
from train_logistic_validation import FEATURES, load_saved_logistic

ROOT = Path(__file__).resolve().parents[2]
METHODS = ['popularity','personal_frequency','weighted_recency','logistic_regression','boosted_trees']


def fingerprint(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda:handle.read(1024*1024),b''):
            digest.update(block)
    return digest.hexdigest()


def announce(message):
    print(message,flush=True)


def prepare():
    checks = ROOT/'05_Results/03_Checks'
    outputs = ROOT/'02_Data/03_Model_Outputs'
    destination = outputs/'final_predictions.sqlite'
    working = outputs/'final_predictions.building.sqlite'
    # Never overwrite the frozen run or quietly replace an interrupted build.
    if destination.exists() or working.exists():
        raise FileExistsError('Final prediction artifact already exists. Review it instead of overwriting.')
    checked = json.loads((checks/'ml_feature_preparation.json').read_text(encoding='utf-8'))
    assert checked['status']=='passed' and checked['feature_columns']==FEATURES
    sources = [ROOT/'02_Data/02_Prepared/evaluation_plan.csv',ROOT/'02_Data/01_Original/orders.csv',
               ROOT/'02_Data/01_Original/order_products__prior.csv']
    source_hashes = {str(p.relative_to(ROOT)):fingerprint(p) for p in sources}
    assert source_hashes==checked['source_sha256']
    frozen_paths = [outputs/'logistic_model.json',outputs/'boosted_trees_model.joblib']
    model_hashes = {str(p.relative_to(ROOT)):fingerprint(p) for p in frozen_paths}
    code_paths = [Path(__file__).resolve(),ROOT/'03_Code/04_Final_Evaluation/final_features.sql',
                  ROOT/'03_Code/03_Model_Comparison/train_logistic_validation.py',ROOT/'01_Project/03_Data_And_Methods.md']
    code_hashes = {str(p.relative_to(ROOT)):fingerprint(p) for p in code_paths}
    report_path = checks/'final_prediction_preparation.json'
    report = {'status':'started','stage':'prediction only; final answers not read',
              'selected_default':'weighted_recency','methods':METHODS,'model_refit':False,
              'source_sha256':source_hashes,'model_sha256':model_hashes,'code_and_plan_sha256':code_hashes,
              'final_answers_read':False,'final_scores_generated':False}
    report_path.write_text(json.dumps(report,indent=2),encoding='utf-8')
    started = time.perf_counter()
    logistic,state = load_saved_logistic(outputs,checks)
    trees = joblib.load(outputs/'boosted_trees_model.joblib')
    models = {'logistic_regression':logistic,'boosted_trees':trees}
    fitted_digests = {k:hashlib.sha256(pickle.dumps(m)).hexdigest() for k,m in models.items()}
    with sqlite3.connect(working.as_uri(),uri=True) as con, threadpool_limits(limits=2):
        con.execute('PRAGMA cache_size=-131072')
        con.create_function('POWER',2,math.pow,deterministic=True)
        con.execute('ATTACH DATABASE ? AS source',[(ROOT/'02_Data/02_Prepared/instacart_ml.sqlite').as_uri()+'?mode=ro'])
        assert con.execute("SELECT value FROM source.build_metadata WHERE key='features_checked'").fetchone()==('passed',)
        con.execute('''CREATE TABLE targets AS SELECT user_id,final_target_order_id AS target_order_id,
            final_history_max_order_number AS history_max_order FROM source.evaluation_plan''')
        con.execute('CREATE UNIQUE INDEX final_users ON targets(user_id)')
        con.execute('CREATE UNIQUE INDEX final_targets ON targets(target_order_id)')
        targets = {r[0]:(r[1],r[2]) for r in con.execute('SELECT * FROM targets')}
        assert len(targets)==131209
        # Verify final order metadata and the complete allowed prior sequence, without product answers.
        found = set()
        sample_ids = set(sorted(targets)[:100])
        raw_sample_orders = {}
        with sources[1].open(encoding='utf-8-sig',newline='') as handle:
            for row in csv.DictReader(handle):
                uid = int(row['user_id'])
                if uid not in targets:
                    continue
                oid,number = int(row['order_id']),int(row['order_number'])
                target,cutoff = targets[uid]
                if oid==target:
                    assert row['eval_set']=='train' and number==cutoff+1
                    found.add(uid)
                if uid in sample_ids and row['eval_set']=='prior' and number<=cutoff:
                    raw_sample_orders[oid]=(uid,number)
        assert found==set(targets)
        histories = con.execute('''SELECT t.user_id,COUNT(o.order_id),MIN(o.order_number),MAX(o.order_number)
            FROM targets t LEFT JOIN source.orders o ON o.user_id=t.user_id
            AND o.eval_set='prior' AND o.order_number<=t.history_max_order GROUP BY t.user_id''').fetchall()
        assert all(n==targets[uid][1] and low==1 and high==n for uid,n,low,high in histories)
        assert con.execute('''SELECT COUNT(*) FROM source.orders o JOIN targets t
            ON t.target_order_id=o.order_id''').fetchone()[0]==0
        announce('Final metadata checked. Building features from allowed prior orders only...')
        sql = (ROOT/'03_Code/04_Final_Evaluation/final_features.sql').read_text(encoding='utf-8')
        con.execute('CREATE TABLE final_features AS '+sql)
        con.execute('CREATE UNIQUE INDEX final_feature_keys ON final_features(user_id,product_id)')
        con.commit()
        candidate_counts = dict(con.execute('SELECT user_id,COUNT(*) FROM final_features GROUP BY user_id'))
        assert set(candidate_counts)==set(targets)
        assert con.execute('''SELECT COUNT(*) FROM final_features f JOIN targets t USING(user_id)
            WHERE f.history_orders<>t.history_max_order OR f.last_purchase_order>t.history_max_order
            OR f.purchase_orders<1 OR f.purchase_orders>f.history_orders
            OR f.purchase_share<=0 OR f.purchase_share>1
            OR f.orders_since_last_purchase<>t.history_max_order-f.last_purchase_order
            OR f.recency_score<=0 OR f.recency_score>f.purchase_orders+1e-8''').fetchone()[0]==0
        assert 'bought_next' not in {r[1] for r in con.execute('PRAGMA table_info(final_features)')}
        con.execute('''CREATE TABLE recommendations(method TEXT,user_id INTEGER,product_id INTEGER,
            rank INTEGER,score REAL,PRIMARY KEY(method,user_id,rank),UNIQUE(method,user_id,product_id))''')
        # Fixed simple methods use refreshed history, unchanged ranking and tie rules.
        for method,rank in [('personal_frequency','purchase_orders DESC,last_purchase_order DESC,product_id'),
                            ('weighted_recency','recency_score DESC,last_purchase_order DESC,product_id')]:
            score = 'purchase_orders' if method=='personal_frequency' else 'recency_score'
            con.execute(f'''INSERT INTO recommendations WITH ranked AS (
                SELECT user_id,product_id,{score} AS score,ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY {rank}) AS rank
                FROM final_features) SELECT ?,user_id,product_id,rank,score FROM ranked WHERE rank<=5''',[method])
        total_orders = sum(n for _,n,_,_ in histories)
        leaders = con.execute('''SELECT product_id,SUM(purchase_orders) AS n FROM final_features
            GROUP BY product_id ORDER BY n DESC,product_id LIMIT 5''').fetchall()
        assert len(leaders)==5
        con.executemany('INSERT INTO recommendations VALUES (?,?,?,?,?)',[
            ('popularity',uid,pid,rank,n/total_orders) for uid in targets
            for rank,(pid,n) in enumerate(leaders,1)])
        con.commit()
        announce('Simple-method lists saved. Applying frozen ML models to final-history features...')
        batch,current,heaps = [],None,{method:[] for method in models}
        def finish_user():
            if current is None:
                return
            for method,heap in heaps.items():
                for rank,item in enumerate(sorted(heap,reverse=True),1):
                    batch.append((method,current,-item[2],rank,item[0]))
            if len(batch)>=50_000:
                con.executemany('INSERT INTO recommendations VALUES (?,?,?,?,?)',batch)
                batch.clear()
        query = 'SELECT user_id,product_id,last_purchase_order,'+','.join(FEATURES)+' FROM final_features ORDER BY user_id,product_id'
        for chunk in pd.read_sql_query(query,con,chunksize=200_000):
            x = chunk[FEATURES].to_numpy(dtype=np.float64)
            assert np.isfinite(x).all()
            probabilities = {method:model.predict_proba(x)[:,1] for method,model in models.items()}
            assert all(np.isfinite(p).all() and ((p>=0)&(p<=1)).all() for p in probabilities.values())
            keys = chunk[['user_id','product_id','last_purchase_order']].to_numpy(dtype=np.int64)
            for idx,(uid,pid,last) in enumerate(keys):
                uid,pid,last = int(uid),int(pid),int(last)
                if uid!=current:
                    finish_user()
                    current,heaps = uid,{method:[] for method in models}
                for method in models:
                    item = (float(probabilities[method][idx]),last,-pid)
                    if len(heaps[method])<5:
                        heapq.heappush(heaps[method],item)
                    elif item>heaps[method][0]:
                        heapq.heapreplace(heaps[method],item)
        finish_user()
        con.executemany('INSERT INTO recommendations VALUES (?,?,?,?,?)',batch)
        con.commit()
        # Check every list and independently reconstruct 100 users' clues from raw prior CSVs.
        announce('All lists generated. Checking eligibility, lengths and independent raw-history examples...')
        expected_slots = sum(min(5,n) for n in candidate_counts.values())
        summaries = {}
        for method in METHODS:
            lengths = dict(con.execute('SELECT user_id,COUNT(*) FROM recommendations WHERE method=? GROUP BY user_id',[method]))
            assert set(lengths)==set(targets)
            assert all(n==(5 if method=='popularity' else min(5,candidate_counts[uid])) for uid,n in lengths.items())
            summaries[method]={'customers':len(lengths),'suggestion_slots':sum(lengths.values()),
                               'short_lists':sum(n<5 for n in lengths.values())}
        assert con.execute('''SELECT COUNT(*) FROM recommendations r LEFT JOIN final_features f
            ON f.user_id=r.user_id AND f.product_id=r.product_id
            WHERE (r.method<>'popularity' AND f.product_id IS NULL) OR r.rank NOT BETWEEN 1 AND 5
               OR r.score IS NULL''').fetchone()[0]==0
        raw = {uid:[] for uid in sample_ids}
        with sources[2].open(encoding='utf-8-sig') as handle:
            next(handle)
            for line in handle:
                fields = line.split(',',2)
                pair = raw_sample_orders.get(int(fields[0]))
                if pair:
                    raw[pair[0]].append((pair[1],int(fields[1])))
        for uid in sorted(sample_ids):
            cutoff = targets[uid][1]
            purchases = {}
            for number,pid in raw[uid]:
                purchases.setdefault(pid,[]).append(number)
            rows = con.execute('SELECT product_id,last_purchase_order,'+','.join(FEATURES)+' FROM final_features WHERE user_id=? ORDER BY product_id',[uid]).fetchall()
            assert {r[0] for r in rows}==set(purchases)
            for pid,last,n,share,age,score,history in rows:
                nums = purchases[pid]
                assert n==len(nums) and last==max(nums) and history==cutoff
                assert abs(share-len(nums)/cutoff)<1e-12 and age==cutoff-last
                assert abs(score-round(sum(0.5**((cutoff-v)/5) for v in nums),12))<1e-9
            values = np.asarray([r[2:] for r in rows],dtype=np.float64)
            portable = expit(((values-np.asarray(state['mean']))/np.asarray(state['scale'])) @ np.asarray(state['coefficients'])+state['intercept'])
            assert np.allclose(portable,logistic.predict_proba(values)[:,1],atol=1e-12)
            for method in METHODS:
                if method=='popularity':
                    expected = [pid for pid,_ in leaders]
                elif method=='personal_frequency':
                    expected = [r[0] for r in sorted(rows,key=lambda r:(-r[2],-r[1],r[0]))[:5]]
                elif method=='weighted_recency':
                    expected = [r[0] for r in sorted(rows,key=lambda r:(-r[5],-r[1],r[0]))[:5]]
                else:
                    probs = models[method].predict_proba(values)[:,1]
                    expected = [r[0] for r,p in sorted(zip(rows,probs),key=lambda pair:(-pair[1],-pair[0][1],pair[0][0]))[:5]]
                actual = [r[0] for r in con.execute('SELECT product_id FROM recommendations WHERE method=? AND user_id=? ORDER BY rank',[method,uid])]
                assert expected==actual,(method,uid)
        assert all(hashlib.sha256(pickle.dumps(m)).hexdigest()==fitted_digests[k] for k,m in models.items())
        assert all(fingerprint(ROOT/path)==value for path,value in model_hashes.items())
        con.execute('CREATE TABLE build_metadata(key TEXT PRIMARY KEY,value TEXT)')
        con.executemany('INSERT INTO build_metadata VALUES (?,?)',[
            ('predictions_checked','passed'),('final_answers_read','false'),('selected_default','weighted_recency')])
        con.commit()
        feature_rows = con.execute('SELECT COUNT(*) FROM final_features').fetchone()[0]
    # sqlite3's transaction context commits but doesn't close the Windows file handle.
    con.close()
    # Only the checked, closed artifact becomes the frozen final prediction database.
    working.rename(destination)
    report.update({'status':'passed','predictions_database':str(destination.relative_to(ROOT)),
        'predictions_sha256':fingerprint(destination),'customers':len(targets),
        'feature_rows':feature_rows,'methods_summary':summaries,'eligible_history_orders':total_orders,
        'independent_raw_csv_customers_checked':len(sample_ids),
        'checks':{'prior_cutoffs_and_target_metadata':True,'same_cohort':True,
            'unique_ranks_and_personal_candidates':True,'short_lists_match_candidate_limits':True,
            'independent_features_and_rankings':True,'original_ML_models_unchanged':True},
        'preparation_seconds':round(time.perf_counter()-started,2),
        'limits':'Predictions only. No final answers, scores, calibration or live-benefit measurements. Popularity may suggest unfamiliar products.'})
    report_path.write_text(json.dumps(report,indent=2),encoding='utf-8')
    announce('Final predictions checked and frozen. Final product answers have not been opened by this script.')
    announce(json.dumps(summaries,indent=2))


if __name__=='__main__':
    prepare()
