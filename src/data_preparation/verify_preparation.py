# Load the Python tools used by this script.
from pathlib import Path
import hashlib,json,re
import duckdb,nbformat
from nbclient import NotebookClient

# Find the project folder so paths work from different starting locations.
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'02_Data/02_Prepared'
AUDIT=ROOT/'05_Results/03_Checks'
# Calculate a fingerprint to detect changes to a saved file.
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(4*1024*1024),b''):h.update(chunk)
    return h.hexdigest()

# Check that prepared files and original sources still match their saved fingerprints.
manifest=json.loads((AUDIT/'prepared_manifest.json').read_text(encoding='utf-8'))
for name,expected in manifest.items():assert sha(OUT/name)==expected,name
source=json.loads((AUDIT/'source_manifest.json').read_text(encoding='utf-8'))
for name,info in source['files'].items():assert sha(ROOT/'02_Data/01_Original'/name)==info['sha256'],name

# Open the prepared database without changing it.
with duckdb.connect(str(OUT/'instacart.duckdb'),read_only=True) as con:
    # Recompute reorder flags from each selected user's sequence, including labelled final orders.
    sampled=con.execute('''WITH history AS (
        SELECT o.user_id,o.order_number,i.product_id,i.reordered,
            MIN(o.order_number) OVER(PARTITION BY o.user_id,i.product_id) AS first_purchase_number
        FROM known_items i JOIN orders o USING(order_id) WHERE o.user_id%1000=1)
        SELECT COUNT(*),COUNT(DISTINCT user_id),
            COUNT(*) FILTER(WHERE reordered!=CAST(order_number>first_purchase_number AS INTEGER)) FROM history''').fetchone()
    assert sampled[2]==0,sampled
    # Check that both cutoffs refer to the intended earlier/later sequence and every train user is represented.
    invalid=con.execute('''SELECT COUNT(*) FROM evaluation_plan e
        JOIN orders v ON v.order_id=e.validation_order_id JOIN orders t ON t.order_id=e.final_target_order_id
        WHERE v.user_id!=e.user_id OR t.user_id!=e.user_id OR v.eval_set!='prior' OR t.eval_set!='train'
          OR e.validation_history_max_order_number!=v.order_number-1
          OR e.final_history_max_order_number!=t.order_number-1 OR t.order_number!=v.order_number+1''').fetchone()[0]
    assert invalid==0
    assert con.execute('SELECT COUNT(*)=COUNT(DISTINCT user_id) FROM evaluation_plan').fetchone()[0]
    # Compare the first selected user's raw basket against the readable sample without losing product rows.
    missing=con.execute('''SELECT COUNT(*) FROM (
        (SELECT o.order_number,i.order_id,i.product_id,i.add_to_cart_order,i.reordered
         FROM order_products__prior i JOIN orders o USING(order_id) WHERE o.user_id=1 AND o.order_number<=3)
        EXCEPT ALL SELECT order_number,order_id,product_id,add_to_cart_order,reordered FROM learning_order_items)''').fetchone()[0]
    assert missing==0
    # Run the three introductory SQL exercises to check they still work.
    queries=0
    for q in (ROOT/'03_Code/01_Data_Preparation/sql_practice.sql').read_text(encoding='utf-8').split(';'):
        if q.strip():con.execute(q).fetchall();queries+=1
    assert queries==3

# Check that the HTML guide links point to existing files and sections.
home=(ROOT/'00_START_HERE.html').read_text(encoding='utf-8')
links=re.findall(r'href="([^"]+)"',home)
for href in links:
    if href.startswith('#'):assert f'id="{href[1:]}"' in home,href
    elif not href.startswith(('https://','http://')):assert (ROOT/href).exists(),href
assert 'REES46' not in home
assert 'Viewed product' not in home
assert 'My case brief' not in home
# Run the introductory notebook and save a separate executed copy.
nbpath=ROOT/'04_Learning/03_Notebooks/01_Data_And_SQL.ipynb'
nb=nbformat.read(nbpath,as_version=4);nbformat.validate(nb)
executed=NotebookClient(nb,timeout=180,kernel_name='python3',resources={'metadata':{'path':str(ROOT)}}).execute()
nbformat.write(executed,AUDIT/'learning_notebook_execution.ipynb')
# Save the verification results; passing checks do not establish business impact.
report={'status':'passed','sampled_users_with_independently_checked_reorder_flags':sampled[1],
        'sampled_product_lines_checked':sampled[0],'reorder_flag_mismatches':sampled[2],
        'evaluation_cutoff_errors':invalid,'sql_exercises_run':queries,'guide_links_checked':len(links),
        'notebook':'all code cells executed successfully',
        'note':'These are preparation checks. Source representativeness and actual recommendation impact are not established.'}
(AUDIT/'verification_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
