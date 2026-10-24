"""Prepare frozen discovery audit lists, then score them in a separate invocation."""
from pathlib import Path
from collections import defaultdict
import argparse
import importlib.util
import json
import math
import random
import sqlite3
import statistics

ROOT=Path(__file__).resolve().parents[2]
CHECKS=ROOT/'05_Results/03_Checks'
CODE=ROOT/'03_Code/03_Model_Comparison/evaluate_discovery.py'
spec=importlib.util.spec_from_file_location('frozen_discovery',CODE)
d=importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)
PROTOCOL=CHECKS/'discovery_audit_protocol.json'
PREP=CHECKS/'discovery_audit_preparation.json'
REPORT=CHECKS/'discovery_audit.json'
OUT=ROOT/'02_Data/03_Model_Outputs/discovery_audit.sqlite'
DEV=ROOT/'02_Data/03_Model_Outputs/discovery_development.sqlite'
POP=ROOT/'02_Data/02_Prepared/discovery_popularity.sqlite'
SOURCE=ROOT/'02_Data/01_Original/order_products__prior.csv'

def ro(p): return sqlite3.connect(p.as_uri()+'?mode=ro',uri=True)
def load(p): return json.loads(p.read_text(encoding='utf-8'))
def verify():
    report=load(CHECKS/'discovery_development.json')
    protocol=load(CHECKS/'discovery_protocol.json')
    assert report['passes_exploratory_gate']
    for p,h in [(CODE,report['code_sha256']),(CHECKS/'discovery_protocol.json',report['protocol_sha256']),
                (DEV,report['predictions_sha256']),(d.DB,protocol['history_source_sha256']),(POP,protocol['popularity_sha256'])]:
        assert d.digest(p)==h, str(p)
    return protocol

def inputs():
    # Audit shoppers contribute personal history only, never shared model fitting.
    with ro(d.DB) as con:
        customers=dict(con.execute("SELECT user_id,target_order_id FROM customers WHERE split='audit' ORDER BY user_id"))
        rows=defaultdict(list)
        for uid,p,score,last in con.execute("SELECT f.user_id,f.product_id,f.recency_score,f.last_purchase_order FROM timing_features f JOIN customers c USING(user_id) WHERE c.split='audit'"):
            rows[uid].append((p,score,last))
        assert con.execute("SELECT COUNT(*) FROM customers WHERE split='development' AND user_id IN (SELECT user_id FROM customers WHERE split='audit')").fetchone()[0]==0
    assert len(customers)==len(rows)==15000
    return customers,rows

def prepare():
    if any(p.exists() for p in (PROTOCOL,PREP,OUT,REPORT)):
        raise FileExistsError('Audit artifacts exist; no overwrite.')
    original=verify()
    # Freeze the same rule and criteria before any audit product answer is read.
    protocol={'stage':'discovery_reserved_audit','authorisation':'Justin requested this final check after reviewing development results.',
        'customers':15000,'target':'Last known prior basket for fixed audit customer IDs; official final test contents remain unknown.',
        'methods':'Unchanged development-fitted neighbours and popularity; no refitting or audit contribution to shared statistics.',
        'personal_inputs':'Earlier audit shopper history only, same fixed seed/score/filter/fallback/tie rules.',
        'metrics':original['metrics'],'gate':original['gate'],
        'gate_interpretation':'Same thresholds retained before audit scoring. Passing supports a prototype experiment, not proven customer benefit.',
        'exposure':'Reserved from V2/V3 development scoring; source previously loaded and summarised. Not new data or guaranteed pristine original source.',
        'limits':original['limits'], 'after_scoring':'Audit becomes exposed. No tuning or repeat fresh-test claims. V2 timing remains stopped; this is a separate discovery audit.',
        'hashes':{str(p.relative_to(ROOT)):d.digest(p) for p in [CODE,Path(__file__),d.DB,DEV,POP,CHECKS/'discovery_protocol.json',CHECKS/'discovery_development.json']}}
    protocol['metrics']=dict(protocol['metrics'],primary='Hit@3 averaged over ALL 15000 audit customers')
    d.save(PROTOCOL,protocol)
    customers,rows=inputs()
    with ro(POP) as con: popularity=[p for p, in con.execute('SELECT product_id FROM popularity ORDER BY rank')]
    neighbours=defaultdict(list)
    with ro(DEV) as con:
        for p,q,s in con.execute('SELECT product_id,related_product_id,similarity FROM neighbours ORDER BY product_id,rank'):
            neighbours[p].append((q,s))
    fallback=0
    with sqlite3.connect(OUT) as out:
        out.execute('CREATE TABLE recommendations(method TEXT,user_id INTEGER,rank INTEGER,product_id INTEGER,PRIMARY KEY(method,user_id,rank),UNIQUE(method,user_id,product_id))')
        out.execute('CREATE TABLE targets(user_id INTEGER PRIMARY KEY,target_order_id INTEGER UNIQUE)')
        out.executemany('INSERT INTO targets VALUES(?,?)',customers.items())
        for uid in customers:
            seen={r[0] for r in rows[uid]}
            scores=defaultdict(float)
            for p,w,_ in sorted(rows[uid],key=lambda r:(-r[1],-r[2],r[0]))[:10]:
                for q,s in neighbours.get(p,[]):
                    if q not in seen: scores[q]+=w*s
            base=d.select({},seen,popularity)[0]
            related,n=d.select(scores,seen,popularity)
            fallback+=len(related)-n
            for method,ps in zip(d.METHODS,[base,related]):
                assert len(ps)<=3 and len(ps)==len(set(ps)) and not set(ps)&seen
                out.executemany('INSERT INTO recommendations VALUES(?,?,?,?)',[(method,uid,i,p) for i,p in enumerate(ps,1)])
    # Independently reconstruct sampled rankings without using the selector helper.
    with ro(OUT) as out:
        for uid in random.Random(23).sample(sorted(customers),100):
            seen={r[0] for r in rows[uid]}
            baseline=[p for p in popularity if p not in seen][:3]
            contributions=defaultdict(list)
            for p,w,_ in sorted(rows[uid],key=lambda r:(-r[1],-r[2],r[0]))[:10]:
                for q,s in neighbours.get(p,[]):
                    if q not in seen:contributions[q].append(w*s)
            ranked=sorted(contributions,key=lambda q:(-round(sum(contributions[q]),12),q))[:3]
            expected=(ranked+[p for p in baseline if p not in ranked])[:3]
            for method,ps in zip(d.METHODS,[baseline,expected]):
                assert ps==[p for p, in out.execute('SELECT product_id FROM recommendations WHERE method=? AND user_id=? ORDER BY rank',(method,uid))]
        totals=dict(out.execute('SELECT method,COUNT(*) FROM recommendations GROUP BY method'))
    d.save(PREP,{'status':'passed','customers':15000,'prediction_rows':totals,'related_fallback_slots':fallback,
        'independent_ranking_customers':100,'audit_answers_read':False,'protocol_sha256':d.digest(PROTOCOL),'predictions_sha256':d.digest(OUT)})
    print(json.dumps(load(PREP),indent=2),flush=True)

def score():
    if REPORT.exists():raise FileExistsError('Audit already scored; do not overwrite.')
    verify()
    protocol,prep=load(PROTOCOL),load(PREP)
    assert d.digest(PROTOCOL)==prep['protocol_sha256'] and d.digest(OUT)==prep['predictions_sha256']
    for path,h in protocol['hashes'].items():assert d.digest(ROOT/path)==h,path
    assert d.digest(SOURCE)==load(CHECKS/'v2_timing_protocol.json')['source_sha256']['order_products__prior.csv']
    customers,rows=inputs()
    seen={u:{r[0] for r in rs} for u,rs in rows.items()}
    lists={m:defaultdict(set) for m in d.METHODS}
    with ro(OUT) as con:
        assert dict(con.execute('SELECT user_id,target_order_id FROM targets'))==customers
        for m,u,p in con.execute('SELECT method,user_id,product_id FROM recommendations'):lists[m][u].add(p)
    for m in d.METHODS:
        assert set(lists[m])==set(customers)
        assert all(not ps&seen[u] for u,ps in lists[m].items())
    # Only now parse the reserved target products; all predictions are frozen.
    answers={u:set() for u in customers}
    lookup={target:u for u,target in customers.items()}
    with SOURCE.open(encoding='utf-8-sig') as f:
        next(f)
        for line in f:
            order,rest=line.split(',',1)
            uid=lookup.get(int(order))
            if uid is not None:answers[uid].add(int(rest.split(',',1)[0]))
    assert all(answers.values())
    novel={u:answers[u]-seen[u] for u in customers}
    eligible=[u for u in customers if novel[u]]
    matches={m:{u:len(ps&novel[u]) for u,ps in lists[m].items()} for m in d.METHODS}
    overall={m:{'hit_at_3':statistics.mean(int(v>0) for v in matches[m].values()),
        'precision_at_3':statistics.mean(v/3 for v in matches[m].values()),
        'recall_at_3_among_novel_baskets':statistics.mean(matches[m][u]/len(novel[u]) for u in eligible),
        'distinct_suggested_products':len(set().union(*lists[m].values())),
        'short_lists':sum(len(ps)<3 for ps in lists[m].values())} for m in d.METHODS}
    a,b=d.METHODS
    differences=[int(matches[b][u]>0)-int(matches[a][u]>0) for u in customers]
    delta=statistics.mean(differences)*100
    se=statistics.stdev(differences)/math.sqrt(len(differences))*100
    interval=[delta-1.96*se,delta+1.96*se]
    pd=(overall[b]['precision_at_3']-overall[a]['precision_at_3'])*100
    gate=protocol['gate']
    passed=delta>=gate['hit_gain_pp_at_least'] and interval[0]>gate['paired_hit_lower_bound_above'] and pd>=gate['precision_gain_pp_at_least']
    # Independent raw-CSV parsing verifies sampled answers and saved-list matches.
    sample=random.Random(24).sample(sorted(customers),100)
    target_sample={customers[u]:u for u in sample}
    independent={u:set() for u in sample}
    import csv
    with SOURCE.open(newline='',encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            uid=target_sample.get(int(r['order_id']))
            if uid is not None:independent[uid].add(int(r['product_id']))
    for u in sample:
        assert independent[u]==answers[u]
        for m in d.METHODS:assert len(independent[u]&lists[m][u])==matches[m][u]
    with ro(POP) as con:catalogue={p for p, in con.execute('SELECT product_id FROM popularity')}
    assert d.digest(OUT)==prep['predictions_sha256']
    for path,h in protocol['hashes'].items():assert d.digest(ROOT/path)==h,path
    d.save(REPORT,{'status':'passed_technical_checks','customers':15000,
        'customers_with_novel_products':len(eligible),'customers_without_novel_products':15000-len(eligible),
        'novel_target_product_lines':sum(map(len,novel.values())),
        'novel_target_lines_in_candidate_catalogue':sum(len(ps&catalogue) for ps in novel.values()),
        'overall':overall,'related_minus_popularity_hit_pp':delta,'paired_approx_95pct_hit_interval_pp':interval,
        'precision_difference_pp':pd,'passes_fixed_audit_gate':passed,'gate':gate,
        'more_hit_customers':sum(v>0 for v in differences),'fewer_hit_customers':sum(v<0 for v in differences),
        'same_hit_customers':sum(v==0 for v in differences),'related_fallback_slots':prep['related_fallback_slots'],
        'raw_csv_sample_customers_checked':100,'predictions_sha256':prep['predictions_sha256'],
        'protocol_sha256':d.digest(PROTOCOL),'code_sha256':d.digest(Path(__file__)),
        'models_refit':False,'prototype_changed':False,'audit_now_exposed':True,
        'limits':'Retrospective source already summarised; no common calendar, causality or customer-benefit proof. Interval assumes independent shoppers conditional on frozen fitted statistics.',
        'next_step':'Review result; if passed, consider a separately authorised discovery prototype and usability test. No automatic UI change or tuning.'})
    print(json.dumps(load(REPORT),indent=2),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('stage',choices=['prepare','score'])
    args=parser.parse_args()
    prepare() if args.stage=='prepare' else score()
