"""Prepare a separate timing study, then evaluate one fixed rule without tuning V1."""
from array import array
import argparse
import csv
import hashlib
from itertools import groupby
import json
import math
from pathlib import Path
import sqlite3
from statistics import mean, median, stdev
import time

ROOT = Path(__file__).resolve().parents[2]
CHECKS = ROOT / '05_Results/03_Checks'
DB = ROOT / '02_Data/02_Prepared/v2_timing.sqlite'
PROTOCOL = CHECKS / 'v2_timing_protocol.json'
PREPARATION = CHECKS / 'v2_timing_preparation.json'
SEED = 'instacart-v2-timing-20261023'
METHODS = ('weighted_recency', 'timing_bonus')


def announce(message):
    print(message, flush=True)


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')


def features(numbers, cutoff):
    # Count earlier purchases; estimate gaps only with at least two observed intervals.
    assert numbers == sorted(set(numbers)) and numbers[-1] <= cutoff
    n = len(numbers)
    recency = round(sum(0.5 ** ((cutoff - number) / 5) for number in numbers), 12)
    gaps = [b - a for a, b in zip(numbers, numbers[1:])]
    typical = median(gaps) if len(gaps) >= 2 else None
    deviation = median([abs(gap - typical) for gap in gaps]) if typical else None
    reliability = min(len(gaps) / 4, 1) / (1 + deviation / typical) if typical else 0.0
    # The target is the NEXT order, one position after the last available history order.
    ratio = (cutoff + 1 - numbers[-1]) / typical if typical else None
    bonus = 0.5 * reliability * math.exp(-abs(ratio - 1)) if ratio is not None else 0.0
    score = round(recency * (1 + bonus), 12)
    return (n, numbers[-1], cutoff, recency, len(gaps), typical, deviation,
            reliability, ratio, bonus, score)


def self_check():
    # Check regular, irregular, sparse and future-leaking examples before real preparation.
    regular = features([2, 5, 8], 10)
    assert regular[5] == 3 and regular[6] == 0 and regular[8] == 1
    assert regular[9] == 0.25
    assert features([2, 8], 10)[9] == 0
    assert features([8], 10)[10] == features([8], 10)[3]
    assert features([1, 2, 8], 10)[7] < regular[7]
    assert features([1, 2, 3, 4, 5], 5)[9] == 0.5
    try:
        features([2, 11], 10)
    except AssertionError:
        pass
    else:
        raise AssertionError('Future purchase was accepted')
    announce('Synthetic timing, fallback and cutoff checks passed.')


def prepare():
    self_check()
    working = DB.with_suffix('.building.sqlite')
    assert not any(p.exists() for p in [DB, working, PROTOCOL, PREPARATION]), 'V2 preparation exists; review rather than overwrite.'
    started = time.perf_counter()
    raw = ROOT / '02_Data/01_Original'
    manifest = json.loads((CHECKS / 'source_manifest.json').read_text(encoding='utf-8'))
    sources = {name: digest(raw / name) for name in ['orders.csv', 'order_products__prior.csv']}
    assert all(value == manifest['files'][name]['sha256'] for name, value in sources.items())
    announce('Original source hashes match. Reading order metadata only.')
    # Use the separate customer cohort; the final official test baskets remain unknown.
    prior = {}
    finals = {}
    with (raw / 'orders.csv').open(encoding='utf-8-sig', newline='') as handle:
        for row in csv.DictReader(handle):
            uid, number, oid = int(row['user_id']), int(row['order_number']), int(row['order_id'])
            if row['eval_set'] == 'prior':
                prior.setdefault(uid, []).append((number, oid))
            else:
                finals[uid] = row['eval_set']
    with (ROOT / '02_Data/02_Prepared/evaluation_plan.csv').open(newline='', encoding='utf-8') as handle:
        v1 = {int(row['user_id']) for row in csv.DictReader(handle)}
    pool = [uid for uid in finals if finals[uid] == 'test']
    assert len(pool) == 75000 and not set(pool) & v1
    pool.sort(key=lambda uid: (hashlib.sha256(f'{SEED}:{uid}'.encode()).digest(), uid))
    development = set(pool[:60000])
    samples = set(pool[:25] + pool[-25:])
    protocol = {
        'date': '2026-10-23', 'status': 'fixed_before_v2_product_answer_inspection',
        'source_sha256': sources, 'code_sha256': digest(Path(__file__)),
        'split': {'salt': SEED, 'rule': 'Sort SHA256(salt:user_id), user_id; first60000 development, remaining15000 audit',
                  'development': 60000, 'audit': 15000},
        'target': 'Last known prior order; all inputs strictly earlier; official test finals not scored',
        'baseline': 'V1 weighted recency; sum 0.5**((cutoff-order_number)/5), rounded12 decimals',
        'challenger': {'rule': 'baseline*(1+0.5*reliability*exp(-abs(next_gap_ratio-1)))',
                       'typical_gap': 'Median adjacent purchase-order gaps; at least3 earlier purchases',
                       'gap_variability': 'Median absolute deviation of gaps from typical_gap',
                       'reliability': 'min(gap_count/4,1)/(1+gap_MAD/typical_gap)',
                       'next_gap_ratio': '(history_cutoff+1-last_purchase_order)/typical_gap',
                       'missing_timing': 'No bonus; baseline unchanged', 'settings_search': False},
        'ranking': 'Score rounded12 decimals descending; last purchase descending; product ID ascending; up to5 familiar products',
        'metrics': {'primary': 'Mean per-customer Recall@5, full actual distinct basket denominator',
                    'precision': 'Matches/5 including unfilled slots', 'hit_rate': 'Customers with at least1 match/all customers'},
        'prospective_gate': {'recall_gain_pp_at_least': 0.25, 'paired_recall_95pct_lower_bound_above': 0,
                             'precision_gain_pp_at_least': -0.10, 'hit_rate_gain_pp_at_least': -0.25,
                             'note': 'Agent-chosen exploratory project criterion set before results, not an industry standard or agreed business target'},
        'audit_policy': 'Only run audit if all development gates pass; freeze audit predictions before reading target product IDs; no retuning afterward',
        'limitations': ['Previously loaded/summarised dataset, not guaranteed pristine unseen data.',
                       'Different cohort/target point; do not compare to V1 aggregate scores.',
                       'Order positions do not measure consumption, quantities or exact elapsed days.']}
    save_json(PROTOCOL, protocol)
    # Keep target order IDs out of the history lookup, before parsing product IDs.
    max_oid = max(oid for orders in prior.values() for _, oid in orders)
    owner = array('i', [0]) * (max_oid + 1)
    position = array('i', [0]) * (max_oid + 1)
    customers = []
    for uid in pool:
        orders = sorted(prior[uid])
        assert [n for n, _ in orders] == list(range(1, len(orders) + 1))
        target_number, target_id = orders[-1]
        assert target_number >= 3
        customers.append((uid, 'development' if uid in development else 'audit', target_id, target_number, target_number - 1))
        for number, oid in orders[:-1]:
            owner[oid], position[oid] = uid, number
        assert owner[target_id] == 0
    del prior, finals
    con = sqlite3.connect(working)
    con.execute('PRAGMA cache_size=-65536')
    con.executescript('''CREATE TABLE customers(user_id INTEGER PRIMARY KEY,split TEXT NOT NULL,
        target_order_id INTEGER UNIQUE NOT NULL,target_order_number INTEGER NOT NULL,history_orders INTEGER NOT NULL);
        CREATE TABLE history(user_id INTEGER,product_id INTEGER,order_number INTEGER,
        PRIMARY KEY(user_id,product_id,order_number)) WITHOUT ROWID;
        CREATE TABLE timing_features(user_id INTEGER,product_id INTEGER,purchase_orders INTEGER,
        last_purchase_order INTEGER,history_orders INTEGER,recency_score REAL,gap_count INTEGER,
        median_gap REAL,gap_mad REAL,reliability REAL,next_gap_ratio REAL,timing_bonus REAL,timing_score REAL,
        PRIMARY KEY(user_id,product_id)) WITHOUT ROWID;
        CREATE TABLE build_metadata(key TEXT PRIMARY KEY,value TEXT);''')
    con.executemany('INSERT INTO customers VALUES (?,?,?,?,?)', customers)
    batch, sample_raw = [], {}
    retained = 0
    with (raw / 'order_products__prior.csv').open(encoding='utf-8-sig') as handle:
        next(handle)
        for scanned, line in enumerate(handle, 1):
            order_field, rest = line.split(',', 1)
            oid = int(order_field)
            uid = owner[oid] if oid < len(owner) else 0
            if uid:
                pid = int(rest.split(',', 1)[0])
                number = position[oid]
                batch.append((uid, pid, number))
                if uid in samples:
                    sample_raw.setdefault((uid, pid), []).append(number)
            if len(batch) >= 50000:
                con.executemany('INSERT INTO history VALUES (?,?,?)', batch)
                retained += len(batch)
                batch.clear()
                con.commit()
            if scanned % 5000000 == 0:
                announce(f'Read {scanned:,} prior rows; kept history only, never target product IDs.')
    con.executemany('INSERT INTO history VALUES (?,?,?)', batch)
    retained += len(batch)
    con.commit()
    assert scanned == 32434489
    announce(f'History retained: {retained:,} product lines. Calculating purchase gaps.')
    cutoffs = {row[0]: row[4] for row in customers}
    rows = con.execute('SELECT user_id,product_id,order_number FROM history ORDER BY user_id,product_id,order_number')
    batch = []
    total = 0
    for (uid, pid), grouped in groupby(rows, key=lambda row: row[:2]):
        numbers = [row[2] for row in grouped]
        batch.append((uid, pid, *features(numbers, cutoffs[uid])))
        if len(batch) >= 25000:
            con.executemany('INSERT INTO timing_features VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', batch)
            total += len(batch)
            batch.clear()
    con.executemany('INSERT INTO timing_features VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', batch)
    total += len(batch)
    con.commit()
    # Recalculate a raw-record sample using independent numerical expressions.
    for (uid, pid), numbers in sample_raw.items():
        n = sorted(numbers)
        row = con.execute('SELECT * FROM timing_features WHERE user_id=? AND product_id=?', (uid, pid)).fetchone()
        assert row[2] == len(n) and row[3] == max(n) and row[4] == cutoffs[uid]
        assert math.isclose(row[5], math.fsum(2 ** (-(cutoffs[uid] - x) / 5) for x in n), abs_tol=1e-10)
        gaps = sorted(n[i] - n[i - 1] for i in range(1, len(n)))
        if len(gaps) >= 2:
            middle = len(gaps) // 2
            expected = gaps[middle] if len(gaps) % 2 else (gaps[middle - 1] + gaps[middle]) / 2
            assert row[7] == expected and row[10] == (cutoffs[uid] + 1 - max(n)) / expected
        else:
            assert row[7] is None and row[11] == 0 and row[12] == row[5]
    invalid = con.execute('''SELECT COUNT(*) FROM timing_features f JOIN customers c USING(user_id)
        WHERE f.history_orders<>c.history_orders OR f.last_purchase_order>=c.target_order_number
        OR f.purchase_orders<1 OR f.purchase_orders>f.history_orders OR gap_count<>purchase_orders-1
        OR timing_bonus<0 OR timing_bonus>0.50000000001 OR timing_score<recency_score
        OR (purchase_orders<3 AND (median_gap IS NOT NULL OR timing_bonus<>0))''').fetchone()[0]
    assert invalid == 0
    assert con.execute('SELECT COUNT(DISTINCT user_id) FROM timing_features').fetchone()[0] == 75000
    con.execute("INSERT INTO build_metadata VALUES ('features_checked','passed')")
    con.execute("INSERT INTO build_metadata VALUES ('protocol_sha256',?)", [digest(PROTOCOL)])
    con.commit()
    groups = [dict(zip(['split', 'customers', 'candidates', 'timing_available'], row)) for row in con.execute('''
        SELECT split,COUNT(DISTINCT user_id),COUNT(*),SUM(median_gap IS NOT NULL)
        FROM timing_features JOIN customers USING(user_id) GROUP BY split''')]
    con.close()
    working.rename(DB)
    save_json(PREPARATION, {'status': 'passed', 'customers': 75000, 'candidate_rows': total,
        'retained_history_product_lines': retained, 'groups': groups, 'raw_sample_customers': len(samples),
        'raw_sample_candidates_checked': len(sample_raw), 'invalid_rows': invalid,
        'target_product_ids_parsed_or_stored': False, 'source_sha256': sources,
        'protocol_sha256': digest(PROTOCOL), 'code_sha256': digest(Path(__file__)),
        'database_sha256': digest(DB), 'seconds': time.perf_counter() - started,
        'model_fitted': False, 'audit_answers_scored': False, 'version_1_modified': False})
    announce(f'V2 preparation passed: {total:,} candidates. No target answers stored or scored.')


def evaluate(stage):
    # Keep development and audit separate, and never score a failed development rule on audit.
    protocol = json.loads(PROTOCOL.read_text(encoding='utf-8'))
    prep = json.loads(PREPARATION.read_text(encoding='utf-8'))
    assert prep['status'] == 'passed' and digest(PROTOCOL) == prep['protocol_sha256']
    assert digest(Path(__file__)) == prep['code_sha256'], 'Evaluation code changed since preparation'
    if stage == 'audit':
        development = json.loads((CHECKS / 'v2_timing_development.json').read_text(encoding='utf-8'))
        assert development['passes_prospective_gate'], 'Development gate failed; audit remains unused'
    out = ROOT / f'02_Data/03_Model_Outputs/v2_timing_{stage}.sqlite'
    report_path = CHECKS / f'v2_timing_{stage}.json'
    assert not out.exists() and not report_path.exists(), 'Saved V2 evaluation exists; do not overwrite'
    assert digest(DB) == prep['database_sha256']
    source = sqlite3.connect(DB.as_uri() + '?mode=ro', uri=True)
    assert source.execute("SELECT value FROM build_metadata WHERE key='features_checked'").fetchone()[0] == 'passed'
    customers = {uid: (target, cutoff) for uid, target, cutoff in source.execute(
        'SELECT user_id,target_order_id,history_orders FROM customers WHERE split=?', [stage])}
    con = sqlite3.connect(out)
    con.executescript('''CREATE TABLE recommendations(method TEXT,user_id INTEGER,rank INTEGER,
        product_id INTEGER,score REAL,PRIMARY KEY(method,user_id,rank));
        CREATE TABLE build_metadata(key TEXT PRIMARY KEY,value TEXT);''')
    selected = {method: {} for method in METHODS}
    rows = source.execute('''SELECT f.user_id,f.product_id,f.recency_score,f.timing_score,f.last_purchase_order
        FROM timing_features f JOIN customers c USING(user_id) WHERE c.split=? ORDER BY f.user_id,f.product_id''', [stage])
    changed = short = 0
    for uid, grouped in groupby(rows, key=lambda row: row[0]):
        candidates = list(grouped)
        lists = {}
        for method, column in [('weighted_recency', 2), ('timing_bonus', 3)]:
            ranked = sorted(candidates, key=lambda row: (-row[column], -row[4], row[1]))[:5]
            lists[method] = [row[1] for row in ranked]
            selected[method][uid] = set(lists[method])
            con.executemany('INSERT INTO recommendations VALUES (?,?,?,?,?)',
                [(method, uid, rank, row[1], row[column]) for rank, row in enumerate(ranked, 1)])
        changed += lists[METHODS[0]] != lists[METHODS[1]]
        short += len(candidates) < 5
    source.close()
    assert all(set(selected[method]) == set(customers) for method in METHODS)
    # Save and fingerprint both lists BEFORE opening target product answers.
    con.execute("INSERT INTO build_metadata VALUES ('predictions_saved_before_answers','true')")
    con.execute("INSERT INTO build_metadata VALUES ('protocol_sha256',?)", [digest(PROTOCOL)])
    con.commit()
    con.close()
    frozen = digest(out)
    answer_source = ROOT / '02_Data/01_Original/order_products__prior.csv'
    assert digest(answer_source) == protocol['source_sha256']['order_products__prior.csv']
    target_to_user = {target: uid for uid, (target, _) in customers.items()}
    answers = {uid: set() for uid in customers}
    announce(f'{stage}: predictions saved. Reading only this split\'s target product IDs for scoring.')
    with answer_source.open(encoding='utf-8-sig') as handle:
        next(handle)
        for line in handle:
            order_field, rest = line.split(',', 1)
            uid = target_to_user.get(int(order_field))
            if uid is not None:
                answers[uid].add(int(rest.split(',', 1)[0]))
    assert all(answers.values())
    scores = {method: {} for method in METHODS}
    differences = []
    more = equal = fewer = 0
    for uid, basket in answers.items():
        counts = []
        for method in METHODS:
            matches = len(selected[method][uid] & basket)
            counts.append(matches)
            scores[method][uid] = (matches / 5, matches / len(basket), int(matches > 0))
        difference = scores[METHODS[1]][uid][1] - scores[METHODS[0]][uid][1]
        differences.append(difference)
        more += counts[1] > counts[0]
        equal += counts[1] == counts[0]
        fewer += counts[1] < counts[0]
    metrics = ['precision_at_5', 'recall_at_5', 'hit_at_5']
    overall = {method: {name: mean(row[i] for row in values.values()) for i, name in enumerate(metrics)}
               for method, values in scores.items()}
    delta = {name: (overall[METHODS[1]][name] - overall[METHODS[0]][name]) * 100 for name in metrics}
    se = stdev(differences) / math.sqrt(len(differences))
    interval = [(mean(differences) - 1.96 * se) * 100, (mean(differences) + 1.96 * se) * 100]
    gate = protocol['prospective_gate']
    passes = (delta['recall_at_5'] >= gate['recall_gain_pp_at_least'] and interval[0] > 0
              and delta['precision_at_5'] >= gate['precision_gain_pp_at_least']
              and delta['hit_at_5'] >= gate['hit_rate_gain_pp_at_least'])
    groups = []
    for label, lo, hi in [('1-5', 1, 5), ('6-15', 6, 15), ('16+', 16, 100000)]:
        ids = [uid for uid, (_, cutoff) in customers.items() if lo <= cutoff <= hi]
        groups.append({'history_orders': label, 'customers': len(ids), 'methods': {
            method: {name: mean(scores[method][uid][i] for uid in ids) for i, name in enumerate(metrics)}
            for method in METHODS}})
    assert digest(out) == frozen and digest(DB) == prep['database_sha256']
    # Independently re-read saved lists for 100 customers and recompute their matches.
    with sqlite3.connect(out.as_uri() + '?mode=ro', uri=True) as saved:
        for uid in sorted(customers)[:100]:
            for method in METHODS:
                ids = {row[0] for row in saved.execute('SELECT product_id FROM recommendations WHERE method=? AND user_id=?', [method, uid])}
                assert len(ids & answers[uid]) / 5 == scores[method][uid][0]
    save_json(report_path, {'status': 'passed', 'stage': stage, 'customers': len(customers),
        'overall': overall, 'timing_minus_recency_pp': delta,
        'recall_paired_approx_95pct_interval_pp': interval,
        'interval_assumption': 'Independent customers; does not establish causal benefit or remove dataset bias',
        'passes_prospective_gate': passes, 'gate': gate, 'history_groups': groups,
        'more_matches': more, 'equal_matches': equal, 'fewer_matches': fewer,
        'changed_ranked_lists': changed, 'short_lists_per_method': short,
        'actual_product_lines': sum(map(len, answers.values())),
        'predictions_sha256': frozen, 'protocol_sha256': digest(PROTOCOL),
        'code_sha256': digest(Path(__file__)), 'sample_saved_matches_checked': 100,
        'other_split_answers_parsed': False, 'version_1_modified': False,
        'next_action': ('Freeze and evaluate audit once' if stage == 'development' and passes
                        else 'Stop; keep V1 rule and leave audit unused' if stage == 'development'
                        else 'Review audit without retuning; no automatic prototype replacement')})
    announce(json.dumps({'stage': stage, 'overall': overall, 'difference_pp': delta,
                         'passes_gate': passes, 'reserved_audit_scored': stage == 'audit'}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['self-check', 'prepare', 'development', 'audit'])
    args = parser.parse_args()
    if args.stage == 'self-check':
        self_check()
    elif args.stage == 'prepare':
        prepare()
    else:
        evaluate(args.stage)
