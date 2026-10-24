"""Descriptive top-five follow-up on already exposed discovery baskets. No refit."""
from pathlib import Path
from collections import defaultdict
import hashlib,json,math,random,sqlite3,statistics,time
ROOT=Path(__file__).resolve().parents[2]
CHECKS=ROOT/'05_Results/03_Checks'
OUT=ROOT/'02_Data/03_Model_Outputs/discovery_top_five.sqlite'
PLAN=CHECKS/'discovery_top_five_plan.json'
REPORT=CHECKS/'discovery_top_five.json'
DB=ROOT/'02_Data/02_Prepared/v2_timing.sqlite'
DEV=ROOT/'02_Data/03_Model_Outputs/discovery_development.sqlite'
AUDIT=ROOT/'02_Data/03_Model_Outputs/discovery_audit.sqlite'
POP=ROOT/'02_Data/02_Prepared/discovery_popularity.sqlite'
METHODS=('unfamiliar_popularity','related_products')
def ro(p):return sqlite3.connect(p.as_uri()+'?mode=ro',uri=True)
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for x in iter(lambda:f.read(1024*1024),b''):h.update(x)
 return h.hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def choose(scores,seen,pop):
 ranked=sorted((p for p in scores if p not in seen),key=lambda p:(-round(scores[p],12),p))[:5]
 n=len(ranked)
 for p in pop:
  if len(ranked)==5:break
  if p not in seen and p not in ranked:ranked.append(p)
 return ranked,len(ranked)-n

def main():
 if any(p.exists() for p in [OUT,PLAN,REPORT]):raise FileExistsError('Follow-up exists; no overwrite.')
 start=time.monotonic()
 dev=json.loads((CHECKS/'discovery_development.json').read_text())
 audit=json.loads((CHECKS/'discovery_audit.json').read_text())
 protocol=json.loads((CHECKS/'discovery_protocol.json').read_text())
 for p,h in [(DEV,dev['predictions_sha256']),(AUDIT,audit['predictions_sha256']),(DB,protocol['history_source_sha256']),(POP,protocol['popularity_sha256'])]:assert digest(p)==h
 protected=[DEV,AUDIT,DB,POP,CHECKS/'discovery_development.json',CHECKS/'discovery_audit.json',ROOT/'03_Code/03_Model_Comparison/evaluate_discovery.py',ROOT/'03_Code/04_Final_Evaluation/evaluate_discovery_audit.py']
 hashes={str(p.relative_to(ROOT)):digest(p) for p in protected}
 save(PLAN,{'purpose':'User-requested descriptive measurement of five suggestions to match current UI.',
 'exposure':'Both development and former audit answers already inspected. NOT a fresh final test.',
 'count':5,'ranking':'Exact frozen development neighbours, popularity, seed weights, rounding, ties and fallback; only cutoff increases from 3 to 5.',
 'metrics':{'hit':'At least one match / all shoppers per split','precision':'Matches / 5 averaged over all shoppers','novel_recall':'Matches / novel target product count, averaged only over nonempty novel baskets; report denominator'},
 'no_new_gate':True,'no_tuning_or_refit':True,'original_evidence_sha256':hashes,'code_sha256':digest(Path(__file__))})
 assert choose({1:100,2:3},{1},[1,2,3,4,5,6])[0]==[2,3,4,5,6]
 with ro(POP) as c:pop=[p for p, in c.execute('SELECT product_id FROM popularity ORDER BY rank')]
 catalogue=set(pop);neighbours=defaultdict(list)
 with ro(DEV) as c:
  for p,q,s in c.execute('SELECT product_id,related_product_id,similarity FROM neighbours ORDER BY product_id,rank'):neighbours[p].append((q,s))
 customers={};rows=defaultdict(list)
 with ro(DB) as c:
  customers={u:(split,target) for u,split,target in c.execute('SELECT user_id,split,target_order_id FROM customers ORDER BY user_id')}
  for u,p,w,last in c.execute('SELECT user_id,product_id,recency_score,last_purchase_order FROM timing_features'):rows[u].append((p,w,last))
 assert len(customers)==75000 and len(rows)==75000
 histories={u:{r[0] for r in rs} for u,rs in rows.items()}
 lists={m:{} for m in METHODS};fallback=defaultdict(int)
 with sqlite3.connect(OUT) as out:
  out.execute('CREATE TABLE recommendations(split TEXT,method TEXT,user_id INTEGER,rank INTEGER,product_id INTEGER,PRIMARY KEY(method,user_id,rank),UNIQUE(method,user_id,product_id))')
  for u,(split,_) in customers.items():
   seen=histories[u];scores=defaultdict(float)
   for p,w,_ in sorted(rows[u],key=lambda r:(-r[1],-r[2],r[0]))[:10]:
    for q,s in neighbours.get(p,[]):
     if q not in seen:scores[q]+=w*s
   base,_=choose({},seen,pop);related,n=choose(scores,seen,pop);fallback[split]+=n
   for m,ps in zip(METHODS,[base,related]):
    assert len(ps)<=5 and len(set(ps))==len(ps) and not set(ps)&seen
    lists[m][u]=ps
    out.executemany('INSERT INTO recommendations VALUES(?,?,?,?,?)',[(split,m,u,i,p) for i,p in enumerate(ps,1)])
 frozen=digest(OUT)
 # Every old top-three list must be the exact prefix, for both splits/methods.
 prefix_checks=0
 for path in [DEV,AUDIT]:
  with ro(path) as c:
   for m,u,rank,p in c.execute('SELECT method,user_id,rank,product_id FROM recommendations'):
    assert lists[m][u][rank-1]==p;prefix_checks+=1
 assert prefix_checks==450000
 print('Five-item lists saved; all original top-three prefixes match. Reading exposed answers for descriptive scoring.',flush=True)
 source=ROOT/'02_Data/01_Original/order_products__prior.csv'
 expected=json.loads((CHECKS/'v2_timing_protocol.json').read_text())['source_sha256']['order_products__prior.csv']
 assert digest(source)==expected
 answers={u:set() for u in customers};lookup={target:u for u,(_,target) in customers.items()}
 with source.open(encoding='utf-8-sig') as f:
  next(f)
  for line in f:
   order,rest=line.split(',',1);u=lookup.get(int(order))
   if u is not None:answers[u].add(int(rest.split(',',1)[0]))
 assert all(answers.values())
 novel={u:answers[u]-histories[u] for u in customers}
 result={}
 for split in ['development','audit']:
  ids=[u for u,(s,_) in customers.items() if s==split];eligible=[u for u in ids if novel[u]]
  matches={m:{u:len(set(lists[m][u])&novel[u]) for u in ids} for m in METHODS}
  metrics={m:{'hit_at_5':statistics.mean(int(matches[m][u]>0) for u in ids),
   'precision_at_5':statistics.mean(matches[m][u]/5 for u in ids),
   'recall_at_5_among_novel_baskets':statistics.mean(matches[m][u]/len(novel[u]) for u in eligible),
   'short_lists':sum(len(lists[m][u])<5 for u in ids),'distinct_suggested_products':len({p for u in ids for p in lists[m][u]})} for m in METHODS}
  a,b=METHODS;ds=[int(matches[b][u]>0)-int(matches[a][u]>0) for u in ids]
  delta=statistics.mean(ds)*100;se=statistics.stdev(ds)/math.sqrt(len(ds))*100
  result[split]={'customers':len(ids),'customers_with_novel_products':len(eligible),'customers_without_novel_products':len(ids)-len(eligible),
   'overall':metrics,'related_minus_popularity_hit_pp':delta,'paired_approx_95pct_hit_interval_pp':[delta-1.96*se,delta+1.96*se],
   'more_hit_customers':sum(x>0 for x in ds),'fewer_hit_customers':sum(x<0 for x in ds),'same_hit_customers':sum(x==0 for x in ds),
   'related_fallback_slots':fallback[split],'novel_target_product_lines':sum(len(novel[u]) for u in ids),
   'novel_target_lines_in_catalogue':sum(len(novel[u]&catalogue) for u in ids)}
  # Independent saved-list overlaps for random shoppers in each split.
  with ro(OUT) as c:
   for u in random.Random(25).sample(ids,100):
    for m in METHODS:
     ps={p for p, in c.execute('SELECT product_id FROM recommendations WHERE method=? AND user_id=?',(m,u))}
     assert not ps&histories[u] and len(ps&answers[u])==matches[m][u]
     old=dev if split=='development' else audit
     assert metrics[m]['hit_at_5']>=old['overall'][m]['hit_at_3']
 assert digest(OUT)==frozen
 for path,h in hashes.items():assert digest(ROOT/path)==h
 save(REPORT,{'status':'passed_technical_checks','interpretation':'Descriptive follow-up on exposed baskets, not independent validation. No new pass/fail gate.',
  'display_count':5,'stages':result,'original_top_three_prefix_rows_verified':prefix_checks,'sample_saved_overlap_customers_per_split':100,
  'predictions_sha256':frozen,'plan_sha256':digest(PLAN),'code_sha256':digest(Path(__file__)),
  'models_refit':False,'parameters_tuned':False,'original_reports_unchanged':True,
  'interval_limits':'Independent shoppers conditional on frozen shared statistics; does not correct post-exposure analysis or prove customer benefit.',
  'elapsed_seconds_not_app_latency':time.monotonic()-start})
 print(REPORT.read_text(),flush=True)
if __name__=='__main__':main()
