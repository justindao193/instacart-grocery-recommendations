"""Export discovery for existing A/B examples, without reading basket answers."""
from pathlib import Path
from collections import defaultdict
import csv, hashlib, json, re, sqlite3
ROOT=Path(__file__).resolve().parents[2]
PAGE=ROOT/'03_Code/05_Prototype/buy_again_prototype.html'
DISPLAY_COUNT=5
def ro(p):return sqlite3.connect((ROOT/p).as_uri()+'?mode=ro',uri=True)
def main():
    report=json.loads((ROOT/'05_Results/03_Checks/discovery_audit.json').read_text())
    assert report['passes_fixed_audit_gate']
    dev=ROOT/'02_Data/03_Model_Outputs/discovery_development.sqlite'
    expected=json.loads((ROOT/'05_Results/03_Checks/discovery_development.json').read_text())['predictions_sha256']
    assert hashlib.sha256(dev.read_bytes()).hexdigest()==expected
    # Reuse development-fitted links; A/B only supply their saved earlier history.
    neighbours=defaultdict(list)
    with ro('02_Data/03_Model_Outputs/discovery_development.sqlite') as con:
        for p,q,s in con.execute('SELECT product_id,related_product_id,similarity FROM neighbours ORDER BY product_id,rank'):neighbours[p].append((q,s))
    with ro('02_Data/02_Prepared/discovery_popularity.sqlite') as con:
        popular=[p for p, in con.execute('SELECT product_id FROM popularity ORDER BY rank')]
    lists={};checks={};traces={}
    with ro('02_Data/03_Model_Outputs/final_predictions.sqlite') as con:
        for alias,uid in [('A',1),('B',113)]:
            rows=con.execute('SELECT product_id,recency_score,last_purchase_order FROM final_features WHERE user_id=? ORDER BY recency_score DESC,last_purchase_order DESC,product_id',(uid,)).fetchall()
            seen={r[0] for r in rows};scores=defaultdict(float);contributions=defaultdict(list)
            for p,w,_ in rows[:10]:
                for q,s in neighbours.get(p,[]):
                    if q not in seen:
                        scores[q]+=w*s
                        contributions[q].append({'seed_product_id':p,'personal_weight':w,'similarity':s,'points':w*s})
            ranked=sorted(scores,key=lambda p:(-round(scores[p],12),p))[:DISPLAY_COUNT]
            n=len(ranked)
            for p in popular:
                if len(ranked)==DISPLAY_COUNT:break
                if p not in seen and p not in ranked:ranked.append(p)
            assert len(set(ranked))==DISPLAY_COUNT and not set(ranked)&seen
            traces[alias]={pid:{'score':scores.get(pid,0),'contributions':contributions.get(pid,[])} for pid in ranked}
            lists[alias]=ranked;checks[alias]={'familiar_overlap':0,'related_slots':n,'popularity_fill_slots':DISPLAY_COUNT-n}
    # No duplicated recommendation row for simulated C: retain its popular section.
    lists['C']=[]
    wanted=set(lists['A']+lists['B']);catalogue={}
    groups={'7':'drinks','16':'dairy','17':'household','3':'bakery','4':'veg'}
    with (ROOT/'02_Data/01_Original/products.csv').open(newline='',encoding='utf-8') as f:
        for r in csv.DictReader(f):
            pid=int(r['product_id'])
            if pid in wanted:catalogue[pid]=[r['product_name'],'fruit' if (r['aisle_id']=='24' or pid==6184) else groups.get(r['department_id'],'pantry'),'']
    assert set(catalogue)==wanted
    payload={'shoppers':lists,'catalogue':catalogue}
    page=PAGE.read_text(encoding='utf-8')
    # Keep the original browse catalogue available for the existing V1 study links.
    block='/* DISCOVERY_START */\nconst ORIGINAL_BROWSE_IDS = Object.keys(P).map(Number);\nconst DISCOVERY_DATA = '+json.dumps(payload,separators=(',',':'))+';\nfor (const [id, item] of Object.entries(DISCOVERY_DATA.catalogue)) { if (!P[id]) P[id] = item; }\n/* DISCOVERY_END */'
    if '/* DISCOVERY_START */' in page:page=re.sub(r'/\* DISCOVERY_START \*/.*?/\* DISCOVERY_END \*/',lambda _:block,page,flags=re.S)
    else:page=page.replace('/* DEMO_DATA_END */','/* DEMO_DATA_END */\n'+block)
    PAGE.write_text(page,encoding='utf-8')
    (ROOT/'05_Results/03_Checks/discovery_demo_export.json').write_text(json.dumps({'status':'passed','display_count':DISPLAY_COUNT,'evaluation_count':3,'examples':checks,'products':payload,'score_trace':traces,'answers_read':False,'model_refitted':False,'note':'A/B are illustrative existing V1 examples, not audit cohort examples; C has no discovery row. Five-item presentation extension; original evaluation remains @3. Photos are managed separately.'},indent=2)+'\n')
    print(json.dumps(payload,indent=2))
if __name__=='__main__':main()
