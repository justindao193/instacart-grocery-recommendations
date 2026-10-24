"""One fixed, exploratory discovery comparison. Never scores the audit cohort."""
from pathlib import Path
from collections import defaultdict
import hashlib
import json
import math
import sqlite3
import statistics
import time
import numpy as np
from scipy.sparse import csr_matrix

ROOT = Path(__file__).resolve().parents[2]
CHECKS = ROOT / '05_Results/03_Checks'
DB = ROOT / '02_Data/02_Prepared/v2_timing.sqlite'
OUT = ROOT / '02_Data/03_Model_Outputs/discovery_development.sqlite'
PROTOCOL = CHECKS / 'discovery_protocol.json'
REPORT = CHECKS / 'discovery_development.json'
METHODS = ('unfamiliar_popularity', 'related_products')

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')

def select(scores, seen, popularity):
    # Familiar products are removed before selection; popularity fills gaps.
    ranked = sorted((p for p in scores if p not in seen), key=lambda p: (-round(scores[p], 12), p))[:3]
    related_count = len(ranked)
    for p in popularity:
        if len(ranked) == 3:
            break
        if p not in seen and p not in ranked:
            ranked.append(p)
    return ranked, related_count

def self_check():
    assert select({1: 100, 2: 2, 3: 2}, {1}, [1, 4, 5])[0] == [2, 3, 4]
    assert select({}, {1, 2}, [1, 2, 3])[0] == [3]
    assert select({1: 2}, {1}, [1])[0] == []
    # Independent dot products confirm the sparse binary co-buyer calculation.
    x = csr_matrix(np.array([[1, 1, 0], [1, 1, 1], [0, 1, 1]], dtype=np.float64))
    counts = np.asarray(x.sum(axis=0)).ravel()
    dot = (x.T @ x).toarray()
    assert dot[0, 1] / math.sqrt(counts[0] * counts[1]) == 2 / math.sqrt(6)
    assert dot[0, 2] == 1

def main():
    self_check()
    if any(p.exists() for p in (OUT, PROTOCOL, REPORT)):
        raise FileExistsError('Frozen discovery attempt already exists; do not overwrite it.')
    start = time.monotonic()
    prep = json.loads((CHECKS / 'v2_timing_preparation.json').read_text())
    assert digest(DB) == prep['database_sha256']
    # Fix all settings and the exploratory gate before this task reads answers.
    protocol = {
        'version': 3, 'stage': 'development_only', 'customers': 60000,
        'data_exposure': 'Development target answers previously scored for V2; exploratory reuse, not fresh validation.',
        'history_source_sha256': digest(DB), 'code_sha256': digest(Path(__file__)),
        'baseline': 'Development history order count, descending; product ID breaks ties. Exclude all personal history before top 3.',
        'challenger': {
            'binary_co_buyer_cosine': 'shared shoppers / sqrt(shoppers buying source * shoppers buying candidate)',
            'minimum_product_shoppers': 50, 'minimum_shared_shoppers': 5,
            'neighbours_per_product': 40, 'personal_seed_products': 10,
            'seed_rank_and_weight': 'Existing five-order-half-life recency, descending; last purchase descending; product ID ascending.',
            'score': 'Sum(seed recency * cosine); round to 12 decimals; product ID breaks ties.',
            'fallback': 'Unfamiliar popularity fills remaining places after related candidates.'},
        'metrics': {'primary': 'Hit@3 averaged over ALL 60000 customers',
                    'precision': 'Matches / 3 for every customer, including short lists',
                    'conditional_novel_recall': 'Matches / novel target products, averaged only over customers with at least one novel target product; report denominator',
                    'novel': 'Absent from complete recorded pre-target personal history'},
        'gate': {'hit_gain_pp_at_least': 0.5, 'paired_hit_lower_bound_above': 0,
                 'precision_gain_pp_at_least': 0, 'note': 'Agent-selected exploratory project criterion, not a business standard. Passing only warrants review; no automatic audit or UI change.'},
        'audit': 'Not read or scored; any audit needs a separate fixed protocol.',
        'limits': 'Per-customer order cutoffs, no shared calendar. Shared histories have cross-customer timing ambiguity. Not causal discovery or satisfaction evidence.'}
    save(PROTOCOL, protocol)
    with sqlite3.connect(DB.as_uri() + '?mode=ro', uri=True) as con:
        assert con.execute("SELECT value FROM build_metadata WHERE key='features_checked'").fetchone()[0] == 'passed'
        customers = dict(con.execute("SELECT user_id,target_order_id FROM customers WHERE split='development' ORDER BY user_id"))
        histories = defaultdict(set)
        seeds = defaultdict(list)
        for uid, pid, score, last in con.execute("""
            SELECT f.user_id,f.product_id,f.recency_score,f.last_purchase_order
            FROM timing_features f JOIN customers c USING(user_id)
            WHERE c.split='development' ORDER BY f.user_id
        """):
            histories[uid].add(pid)
            seeds[uid].append((pid, score, last))
    assert len(customers) == len(histories) == 60000
    popularity_db = ROOT / '02_Data/02_Prepared/discovery_popularity.sqlite'
    protocol['popularity_sha256'] = digest(popularity_db)
    save(PROTOCOL, protocol)
    with sqlite3.connect(popularity_db.as_uri() + '?mode=ro', uri=True) as con:
        popularity = [p for p, in con.execute('SELECT product_id FROM popularity ORDER BY rank')]
    all_products = set(popularity)
    support = defaultdict(int)
    for seen in histories.values():
        for pid in seen:
            support[pid] += 1
    products = sorted(p for p, count in support.items() if count >= 50)
    index = {p: i for i, p in enumerate(products)}
    users = sorted(customers)
    # A sparse table stores only observed shopper/product links, not every zero.
    rr, cc = [], []
    for r, uid in enumerate(users):
        for p in histories[uid]:
            if p in index:
                rr.append(r); cc.append(index[p])
    x = csr_matrix((np.ones(len(rr)), (rr, cc)), shape=(len(users), len(products)))
    del rr, cc
    supports = np.array([support[p] for p in products], dtype=float)
    neighbours = {}
    sample_pairs = []
    print(f'Building related products from {len(products)} supported items; no target answers read.', flush=True)
    # Work in blocks so the complete item-pair matrix needn't stay in memory.
    for first in range(0, len(products), 128):
        block = (x[:, first:first+128].T @ x).tocsr()
        for local in range(block.shape[0]):
            i = first + local
            row = block.getrow(local)
            mask = (row.data >= 5) & (row.indices != i)
            js, counts = row.indices[mask], row.data[mask]
            sim = counts / np.sqrt(supports[i] * supports[js])
            order = np.lexsort((np.array(products)[js], -np.round(sim, 12)))[:40]
            neighbours[products[i]] = [(products[int(js[k])], float(sim[k])) for k in order]
            if len(sample_pairs) < 100 and len(order):
                k = order[0]
                sample_pairs.append((i, int(js[k]), int(counts[k]), float(sim[k])))
        if first % 2048 == 0:
            print(f'Related-product rows: {first}/{len(products)}', flush=True)
    # Check sampled associations directly with independent shopper-set overlaps.
    needed = {products[i] for pair in sample_pairs for i in pair[:2]}
    buyers = {p: set() for p in needed}
    for uid, seen in histories.items():
        for p in seen & needed:
            buyers[p].add(uid)
    for i, j, shared, sim in sample_pairs:
        a, b = buyers[products[i]], buyers[products[j]]
        assert len(a & b) == shared
        assert math.isclose(len(a & b) / math.sqrt(len(a)*len(b)), sim)
    selected = {m: {} for m in METHODS}
    fallback_slots = 0
    with sqlite3.connect(OUT) as out:
        out.execute('CREATE TABLE recommendations(method TEXT,user_id INTEGER,rank INTEGER,product_id INTEGER,PRIMARY KEY(method,user_id,rank),UNIQUE(method,user_id,product_id))')
        out.execute('CREATE TABLE neighbours(product_id INTEGER,rank INTEGER,related_product_id INTEGER,similarity REAL,PRIMARY KEY(product_id,rank))')
        out.executemany('INSERT INTO neighbours VALUES(?,?,?,?)',[(p,r,q,s) for p,ns in neighbours.items() for r,(q,s) in enumerate(ns,1)])
        for uid in users:
            seen = histories[uid]
            selected[METHODS[0]][uid] = select({}, seen, popularity)[0]
            seed_list = sorted(seeds[uid], key=lambda r: (-r[1],-r[2],r[0]))[:10]
            scores = defaultdict(float)
            for p, weight, _ in seed_list:
                for q, similarity in neighbours.get(p, []):
                    if q not in seen:
                        scores[q] += weight * similarity
            ranked, related_count = select(scores, seen, popularity)
            fallback_slots += len(ranked) - related_count
            selected[METHODS[1]][uid] = ranked
            for method in METHODS:
                ps = selected[method][uid]
                assert len(ps) <= 3 and len(ps) == len(set(ps)) and not set(ps) & seen
                assert set(ps) <= all_products
                out.executemany('INSERT INTO recommendations VALUES(?,?,?,?)',[(method,uid,r,p) for r,p in enumerate(ps,1)])
    frozen = digest(OUT)
    print('Both lists saved. Now reading development targets only.', flush=True)
    # Parse product answers only for development target IDs, never audit targets.
    target_to_user = {target: uid for uid, target in customers.items()}
    answers = {uid: set() for uid in users}
    answer_source = ROOT / '02_Data/01_Original/order_products__prior.csv'
    timing_protocol = json.loads((CHECKS/'v2_timing_protocol.json').read_text())
    assert digest(answer_source) == timing_protocol['source_sha256']['order_products__prior.csv']
    with answer_source.open(encoding='utf-8-sig') as f:
        next(f)
        for line in f:
            field, rest = line.split(',', 1)
            uid = target_to_user.get(int(field))
            if uid is not None:
                answers[uid].add(int(rest.split(',', 1)[0]))
    assert all(answers.values())
    novel = {uid: answers[uid] - histories[uid] for uid in users}
    novel_users = [uid for uid in users if novel[uid]]
    measures, hits, matches = {}, {}, {}
    for method in METHODS:
        matches[method] = {uid:len(set(selected[method][uid]) & novel[uid]) for uid in users}
        hits[method] = [int(matches[method][uid] > 0) for uid in users]
        measures[method] = {
            'hit_at_3': statistics.mean(hits[method]),
            'precision_at_3': statistics.mean(matches[method][uid]/3 for uid in users),
            'recall_at_3_among_novel_baskets': statistics.mean(matches[method][uid]/len(novel[uid]) for uid in novel_users),
            'distinct_suggested_products': len({p for ps in selected[method].values() for p in ps}),
            'short_lists': sum(len(ps)<3 for ps in selected[method].values())}
    diffs = [b-a for a,b in zip(hits[METHODS[0]],hits[METHODS[1]])]
    delta = statistics.mean(diffs)*100
    se = statistics.stdev(diffs)/math.sqrt(len(diffs))*100
    interval = [delta-1.96*se, delta+1.96*se]
    precision_delta = (measures[METHODS[1]]['precision_at_3']-measures[METHODS[0]]['precision_at_3'])*100
    passed = delta >= .5 and interval[0]>0 and precision_delta>=0
    with sqlite3.connect(OUT.as_uri()+'?mode=ro', uri=True) as out:
        for uid in users[:100]:
            for method in METHODS:
                ps = {p for p, in out.execute('SELECT product_id FROM recommendations WHERE method=? AND user_id=?',(method,uid))}
                assert len(ps & answers[uid]) == matches[method][uid]
                assert not ps & histories[uid]
    assert digest(OUT) == frozen and digest(DB) == protocol['history_source_sha256']
    save(REPORT, {
        'status': 'passed_technical_checks', 'customers':len(users),
        'customers_with_novel_products':len(novel_users), 'customers_without_novel_products':len(users)-len(novel_users),
        'novel_target_product_lines':sum(map(len,novel.values())),
        'novel_target_lines_in_candidate_catalogue':sum(len(ps & all_products) for ps in novel.values()),
        'overall':measures, 'related_minus_popularity_hit_pp':delta,
        'paired_approx_95pct_hit_interval_pp':interval, 'precision_difference_pp':precision_delta,
        'passes_exploratory_gate':passed, 'gate':protocol['gate'],
        'related_fallback_slots':fallback_slots, 'supported_similarity_products':len(products),
        'independent_association_checks':len(sample_pairs), 'saved_list_overlap_checks_per_method':100,
        'predictions_sha256':frozen,'protocol_sha256':digest(PROTOCOL),'code_sha256':digest(Path(__file__)),
        'audit_used':False, 'prototype_changed':False,
        'interpretation':'Exploratory exposed-development comparison, not causal evidence or final audit. Paired interval assumes independent shoppers with shared fitted statistics treated as fixed.',
        'elapsed_seconds_not_app_latency':time.monotonic()-start,
        'next_step':'Review development result together; no automatic audit scoring or UI change.'})
    print(REPORT.read_text(),flush=True)

if __name__ == '__main__':
    main()
