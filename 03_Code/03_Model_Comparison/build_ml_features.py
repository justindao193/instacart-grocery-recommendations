"""Build and audit local rebuy features with SQLite; never fit a model or read final baskets."""
import csv
import hashlib
import json
import math
from pathlib import Path
import sqlite3
import time

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT/'02_Data/02_Prepared/instacart_ml.sqlite'
CHECKS = ROOT/'05_Results/03_Checks'
FEATURE_COLUMNS = ['purchase_orders','purchase_share','orders_since_last_purchase',
                   'recency_score','history_orders']


def announce(message):
    print(message, flush=True)


def fingerprint(path):
    # Check input bytes before reusing the local SQLite source cache.
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def import_source(con, paths):
    # Keep only evaluation customers and baskets through validation; no final basket contents.
    hashes = {str(p.relative_to(ROOT)): fingerprint(p) for p in paths}
    con.execute('CREATE TABLE IF NOT EXISTS build_metadata (key TEXT PRIMARY KEY,value TEXT)')
    saved = con.execute("SELECT value FROM build_metadata WHERE key='source_hashes'").fetchone()
    if saved:
        if json.loads(saved[0]) != hashes:
            raise RuntimeError('Inputs changed. Review the source cache before rebuilding.')
        announce('Reusing checked SQLite source cache.')
        return hashes
    # Only restart this script's incomplete source tables, never the existing DuckDB file.
    for table in ('order_products__prior','orders','evaluation_plan'):
        con.execute(f'DROP TABLE IF EXISTS {table}')
    con.execute('''CREATE TABLE evaluation_plan (user_id INTEGER PRIMARY KEY,
        validation_order_id INTEGER,validation_history_max_order_number INTEGER,
        final_target_order_id INTEGER,final_history_max_order_number INTEGER)''')
    with paths[0].open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        plan = {int(r['user_id']): tuple(int(r[k]) for k in reader.fieldnames) for r in reader}
    con.executemany('INSERT INTO evaluation_plan VALUES (?,?,?,?,?)', plan.values())
    con.execute('''CREATE TABLE orders (order_id INTEGER PRIMARY KEY,user_id INTEGER NOT NULL,
        eval_set TEXT NOT NULL,order_number INTEGER NOT NULL)''')
    # Use a compact order-ID lookup while streaming CSVs instead of loading all purchase rows.
    included = bytearray(3_500_000)
    batch = []
    with paths[1].open(encoding='utf-8-sig', newline='') as handle:
        for r in csv.DictReader(handle):
            uid, number, oid = int(r['user_id']),int(r['order_number']),int(r['order_id'])
            if uid not in plan or r['eval_set'] != 'prior' or number > plan[uid][2]+1:
                continue
            if oid >= len(included):
                included.extend(bytes(oid+1-len(included)))
            included[oid] = 1
            batch.append((oid,uid,'prior',number))
            if len(batch) >= 50_000:
                con.executemany('INSERT INTO orders VALUES (?,?,?,?)',batch)
                batch.clear()
    con.executemany('INSERT INTO orders VALUES (?,?,?,?)',batch)
    con.execute('CREATE UNIQUE INDEX order_sequence ON orders(user_id,order_number)')
    con.commit()
    announce('Order metadata imported. Reading prior purchase lines...')
    con.execute('''CREATE TABLE order_products__prior (order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,PRIMARY KEY(order_id,product_id)) WITHOUT ROWID''')
    batch = []
    scanned = inserted = 0
    with paths[2].open(encoding='utf-8-sig', newline='') as handle:
        next(handle)
        for line in handle:
            fields = line.split(',',2)
            scanned += 1
            oid = int(fields[0])
            if oid < len(included) and included[oid]:
                batch.append((oid,int(fields[1])))
            if len(batch) >= 50_000:
                con.executemany('INSERT INTO order_products__prior VALUES (?,?)',batch)
                inserted += len(batch)
                batch.clear()
            if scanned % 5_000_000 == 0:
                con.commit()
                announce(f'Read {scanned:,} prior lines; retained {inserted:,} so far.')
    con.executemany('INSERT INTO order_products__prior VALUES (?,?)',batch)
    assert scanned == 32_434_489, scanned
    con.execute("INSERT INTO build_metadata VALUES ('source_hashes',?)",[json.dumps(hashes)])
    con.commit()
    return hashes


def verify(con):
    # Stop on repeated candidates, invalid values or history reaching the answer basket.
    def count(sql):
        return con.execute(sql).fetchone()[0]
    assert count('''SELECT COUNT(*) FROM (SELECT stage,user_id,product_id FROM ml_features
        GROUP BY stage,user_id,product_id HAVING COUNT(*)<>1)''') == 0
    assert count('''SELECT COUNT(*) FROM ml_features WHERE
        history_orders<>history_max_order OR history_orders<1
        OR target_order_number<>history_max_order+1
        OR purchase_orders<1 OR purchase_orders>history_orders
        OR purchase_share<=0 OR purchase_share>1
        OR last_purchase_order>history_max_order OR last_purchase_order<1
        OR orders_since_last_purchase<>history_max_order-last_purchase_order
        OR recency_score<=0 OR recency_score>purchase_orders+0.00000001
        OR bought_next NOT IN (0,1) OR purchase_share IS NULL OR recency_score IS NULL''') == 0
    customers = count('SELECT COUNT(*) FROM evaluation_plan')
    summaries = con.execute('''SELECT stage,COUNT(*),COUNT(DISTINCT user_id),SUM(bought_next)
        FROM ml_features GROUP BY stage ORDER BY stage''').fetchall()
    assert {r[0] for r in summaries} == {'training','validation'}
    assert all(r[2] == customers and 0 < r[3] < r[1] for r in summaries)
    assert count('''SELECT COUNT(*) FROM ml_features f JOIN evaluation_plan e USING(user_id)
        WHERE f.target_order_id=e.final_target_order_id
        OR (stage='training' AND history_max_order<>e.validation_history_max_order_number-1)
        OR (stage='validation' AND (target_order_id<>e.validation_order_id
            OR history_max_order<>e.validation_history_max_order_number))''') == 0
    assert count('''SELECT COUNT(*) FROM orders o JOIN evaluation_plan e USING(user_id)
        WHERE o.order_id=e.final_target_order_id''') == 0
    # Independently reconstruct features/labels for ten customers from original CSVs.
    sample = {r[0] for r in con.execute('SELECT user_id FROM evaluation_plan ORDER BY user_id LIMIT 10')}
    points = con.execute('''SELECT DISTINCT user_id,stage,target_order_id,history_max_order
        FROM ml_features WHERE user_id IN
        (SELECT user_id FROM evaluation_plan ORDER BY user_id LIMIT 10)''').fetchall()
    order_map = {}
    with (ROOT/'02_Data/01_Original/orders.csv').open(encoding='utf-8-sig',newline='') as handle:
        for r in csv.DictReader(handle):
            if int(r['user_id']) in sample and r['eval_set'] == 'prior':
                order_map[int(r['order_id'])] = (int(r['user_id']),int(r['order_number']))
    raw = {uid: [] for uid in sample}
    with (ROOT/'02_Data/01_Original/order_products__prior.csv').open(encoding='utf-8-sig') as handle:
        next(handle)
        for line in handle:
            fields = line.split(',',2)
            pair = order_map.get(int(fields[0]))
            if pair:
                raw[pair[0]].append((pair[1],int(fields[1])))
    for uid,stage,target,cutoff in points:
        purchases,answers = {},set()
        for number,pid in raw[uid]:
            if number<=cutoff:
                purchases.setdefault(pid,[]).append(number)
            elif number==cutoff+1:
                answers.add(pid)
        rows = con.execute('''SELECT product_id,purchase_orders,purchase_share,
            orders_since_last_purchase,recency_score,history_orders,bought_next
            FROM ml_features WHERE user_id=? AND stage=?''',[uid,stage]).fetchall()
        assert {r[0] for r in rows} == set(purchases)
        for pid,n,share,age,score,history,label in rows:
            nums = purchases[pid]
            assert n==len(nums) and history==cutoff
            assert abs(share-len(nums)/cutoff)<1e-12
            assert age==cutoff-max(nums)
            assert abs(score-round(sum(0.5**((cutoff-v)/5) for v in nums),12))<1e-9
            assert label==int(pid in answers)
    announce('Independent raw-CSV checks passed for ten customers, both stages.')
    return summaries


def compare_saved_results(con):
    # Recreate both personal methods and compare all validation scores to saved DuckDB evidence.
    expected = json.loads((CHECKS/'weighted_recency_validation.json').read_text(encoding='utf-8'))
    results = {}
    for method,rank in [
        ('personal_frequency','purchase_orders DESC,last_purchase_order DESC,product_id'),
        ('weighted_recency','recency_score DESC,last_purchase_order DESC,product_id')]:
        scores = con.execute(f'''WITH ranked AS (
            SELECT user_id,bought_next,ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY {rank}) AS rank
            FROM ml_features WHERE stage='validation'
        ), matches AS (SELECT user_id,SUM(bought_next) AS hits FROM ranked WHERE rank<=5 GROUP BY user_id),
        sizes AS (SELECT e.user_id,COUNT(*) AS basket_size FROM evaluation_plan e
            JOIN order_products__prior i ON i.order_id=e.validation_order_id GROUP BY e.user_id)
        SELECT AVG(hits/5.0),AVG(hits*1.0/basket_size),AVG(CAST(hits>0 AS REAL)),COUNT(*)
        FROM matches JOIN sizes USING(user_id)''').fetchone()
        assert scores[3]==expected['customers']
        for metric,value in zip(['precision_at_5','recall_at_5','hit_at_5'],scores):
            assert abs(value-expected['comparison'][metric][method])<1e-10,(method,metric,value)
        results[method] = dict(zip(['precision_at_5','recall_at_5','hit_at_5','customers'],scores))
        announce(f'{method}: SQLite scores match saved DuckDB validation results.')
    return results


def build():
    started = time.monotonic()
    paths = [ROOT/'02_Data/02_Prepared/evaluation_plan.csv',ROOT/'02_Data/01_Original/orders.csv',
             ROOT/'02_Data/01_Original/order_products__prior.csv']
    sql = (ROOT/'03_Code/03_Model_Comparison/ml_features.sql').read_text(encoding='utf-8')
    # Use a new local SQLite file; source CSVs and the old DuckDB database stay unchanged.
    with sqlite3.connect(DB) as con:
        con.execute('PRAGMA cache_size=-131072')
        con.create_function('POWER',2,math.pow,deterministic=True)
        hashes = import_source(con,paths)
        announce('Building training and validation features using SQLite SQL...')
        con.execute("DELETE FROM build_metadata WHERE key='features_checked'")
        con.execute('DROP TABLE IF EXISTS ml_features')
        con.execute('CREATE TABLE ml_features AS '+sql)
        con.execute('CREATE UNIQUE INDEX ml_feature_keys ON ml_features(stage,user_id,product_id)')
        con.commit()
        announce('Feature rows built. Checking cutoffs, values and raw examples...')
        summaries = verify(con)
        comparison = compare_saved_results(con)
        # Write a success report only after every runtime check and comparison passes.
        report = {
            'status':'passed','engine':'Python sqlite3','sqlite_version':sqlite3.sqlite_version,
            'database':str(DB.relative_to(ROOT)),'table':'ml_features',
            'feature_columns':FEATURE_COLUMNS,'label_column':'bought_next',
            'identifiers_and_audit_columns_are_not_model_inputs':True,
            'model_fitted':False,'final_baskets_loaded_or_scored':False,'source_sha256':hashes,
            'stages':[dict(zip(['stage','rows','customers','positive_rows'],r)) for r in summaries],
            'independent_raw_csv_customers_checked':10,
            'saved_validation_result_comparison':comparison,
            'preparation_seconds':round(time.monotonic()-started,2),
            'timing_note':'One preparation run, not a model response-time benchmark.',
            'limits':'Rebuy candidates and known customers only; not customer-benefit evidence.'}
        (CHECKS/'ml_feature_preparation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        con.execute("INSERT OR REPLACE INTO build_metadata VALUES ('features_checked','passed')")
        con.commit()
    announce('SQLite features checked and saved. No model fitted; final baskets untouched.')


if __name__=='__main__':
    build()
