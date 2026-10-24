"""Build learning tables from the unchanged Instacart source CSVs."""
# Load the Python tools used by this script.
from pathlib import Path
import hashlib, json
import duckdb

# Find the project folder so paths work from different starting locations.
ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'02_Data/01_Original'
OUT=ROOT/'02_Data/02_Prepared'
AUDIT=ROOT/'05_Results/03_Checks'

# Calculate a file fingerprint without loading the whole file into memory.
def fingerprint(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(4*1024*1024),b''):h.update(chunk)
    return h.hexdigest()

# Rebuild the prepared tables from the unchanged source CSV files.
def prepare():
    OUT.mkdir(parents=True,exist_ok=True)
    AUDIT.mkdir(parents=True,exist_ok=True)
    # Check source fingerprints before preparing anything.
    manifest=json.loads((AUDIT/'source_manifest.json').read_text(encoding='utf-8'))
    for name,info in manifest['files'].items():
        if fingerprint(RAW/name)!=info['sha256']:raise ValueError(f'Source changed: {name}')
    # Open the local database for rebuilding and set resource limits.
    con=duckdb.connect(str(OUT/'instacart.duckdb'))
    con.execute("SET threads=4")
    con.execute("SET memory_limit='3GB'")
    # Load the six CSVs into database tables.
    for name in ['orders','products','aisles','departments','order_products__prior','order_products__train']:
        print('Loading',name,flush=True)
        con.read_csv(str(RAW/(name+'.csv')),header=True).create_view('source_input',replace=True)
        if name=='orders':
            # Hour values such as 08 may be inferred as text; store the documented numeric codes.
            con.execute('''CREATE OR REPLACE TABLE orders AS SELECT
                CAST(order_id AS BIGINT) AS order_id,CAST(user_id AS BIGINT) AS user_id,eval_set,
                CAST(order_number AS INTEGER) AS order_number,CAST(order_dow AS INTEGER) AS order_dow,
                CAST(order_hour_of_day AS INTEGER) AS order_hour_of_day,
                CAST(days_since_prior_order AS DOUBLE) AS days_since_prior_order FROM source_input''')
        else:
            con.execute(f'CREATE OR REPLACE TABLE {name} AS SELECT * FROM source_input')
    # Compare table sizes with the expected source row counts.
    count=lambda sql:int(con.execute(sql).fetchone()[0])
    counts={name:count(f'SELECT COUNT(*) FROM {name}') for name in ['orders','products','aisles','departments','order_products__prior','order_products__train']}
    expected={'orders':3421083,'products':49688,'aisles':134,'departments':21,'order_products__prior':32434489,'order_products__train':1384617}
    assert counts==expected,(counts,expected)
    # Collect data-quality checks; zero means no issue was found by that check.
    checks={}
    # Check that each main table has a unique, nonblank ID.
    for table,key in [('orders','order_id'),('products','product_id'),('aisles','aisle_id'),('departments','department_id')]:
        checks[f'{table}_duplicate_keys']=count(f'SELECT COUNT(*)-COUNT(DISTINCT {key}) FROM {table}')
        checks[f'{table}_missing_keys']=count(f'SELECT COUNT(*) FROM {table} WHERE {key} IS NULL')
    # Check product rows for duplicate pairs, broken links and invalid values.
    for table,split in [('order_products__prior','prior'),('order_products__train','train')]:
        checks[f'{split}_duplicate_order_product_pairs']=count(f'SELECT COUNT(*) FROM (SELECT order_id,product_id FROM {table} GROUP BY ALL HAVING COUNT(*)>1)')
        checks[f'{split}_invalid_product_links']=count(f'SELECT COUNT(*) FROM {table} x ANTI JOIN products p USING(product_id)')
        checks[f'{split}_invalid_order_links']=count(f'SELECT COUNT(*) FROM {table} x ANTI JOIN orders o USING(order_id)')
        checks[f'{split}_wrong_split_links']=count(f"SELECT COUNT(*) FROM {table} x JOIN orders o USING(order_id) WHERE o.eval_set!='{split}'")
        checks[f'{split}_invalid_values']=count(f'SELECT COUNT(*) FROM {table} WHERE order_id IS NULL OR product_id IS NULL OR reordered NOT IN (0,1) OR reordered IS NULL OR add_to_cart_order IS NULL OR add_to_cart_order<1')
        checks[f'{split}_nonsequential_cart_positions']=count(f'SELECT COUNT(*) FROM (SELECT order_id FROM {table} GROUP BY order_id HAVING MIN(add_to_cart_order)!=1 OR MAX(add_to_cart_order)!=COUNT(*) OR COUNT(DISTINCT add_to_cart_order)!=COUNT(*))')
    # Check customer order sequences, time codes, expected blanks and categories.
    checks['orders_duplicate_user_sequence']=count('SELECT COUNT(*) FROM (SELECT user_id,order_number FROM orders GROUP BY ALL HAVING COUNT(*)>1)')
    checks['orders_invalid_time_codes']=count('SELECT COUNT(*) FROM orders WHERE user_id IS NULL OR order_number<1 OR order_dow NOT BETWEEN 0 AND 6 OR order_hour_of_day NOT BETWEEN 0 AND 23 OR days_since_prior_order NOT BETWEEN 0 AND 30')
    checks['first_order_with_gap']=count('SELECT COUNT(*) FROM orders WHERE order_number=1 AND days_since_prior_order IS NOT NULL')
    checks['later_order_missing_gap']=count('SELECT COUNT(*) FROM orders WHERE order_number>1 AND days_since_prior_order IS NULL')
    checks['products_missing_category_links']=count('SELECT COUNT(*) FROM products p LEFT JOIN aisles a USING(aisle_id) LEFT JOIN departments d USING(department_id) WHERE a.aisle_id IS NULL OR d.department_id IS NULL')
    checks['users_with_nonconsecutive_order_numbers']=count('SELECT COUNT(*) FROM (SELECT user_id FROM orders GROUP BY user_id HAVING MIN(order_number)!=1 OR MAX(order_number)!=COUNT(*))')
    checks['unexpected_eval_sets']=count("SELECT COUNT(*) FROM orders WHERE eval_set NOT IN ('prior','train','test') OR eval_set IS NULL")
    # Structural failures stop preparation. Missing category LABELS are retained and reported separately.
    failures={k:v for k,v in checks.items() if v!=0}
    if failures:
        (AUDIT/'structural_failures.json').write_text(json.dumps(failures,indent=2),encoding='utf-8')
        raise ValueError(f'Review source anomalies before proceeding: {failures}')
    # Add readable aisle and department names to the product catalogue.
    con.execute('''CREATE OR REPLACE TABLE product_catalog AS
        SELECT p.*,a.aisle,d.department FROM products p JOIN aisles a USING(aisle_id) JOIN departments d USING(department_id)''')
    # Combine baskets with known contents; official test basket contents stay unknown.
    con.execute('''CREATE OR REPLACE VIEW known_items AS
        SELECT *, 'prior' AS split FROM order_products__prior UNION ALL
        SELECT *, 'train' AS split FROM order_products__train''')
    # Summarise each known basket without turning unknown baskets into zero-size baskets.
    con.execute('''CREATE OR REPLACE TABLE order_summary AS
        WITH baskets AS (SELECT order_id,COUNT(*) AS product_lines,SUM(reordered) AS repeat_product_lines FROM known_items GROUP BY order_id)
        SELECT o.*,o.eval_set!='test' AS contents_available,b.product_lines,b.repeat_product_lines
        FROM orders o LEFT JOIN baskets b USING(order_id)''')
    assert count("SELECT COUNT(*) FROM order_summary WHERE eval_set!='test' AND product_lines IS NULL")==0
    assert count("SELECT COUNT(*) FROM order_summary WHERE eval_set='test' AND product_lines IS NOT NULL")==0
    # Build descriptive product totals from all prior orders, not validation-safe features.
    con.execute('''CREATE OR REPLACE TABLE product_history_metrics AS
        WITH metrics AS (
            SELECT i.product_id,COUNT(*) AS prior_product_lines,COUNT(DISTINCT o.user_id) AS prior_buyers,
            SUM(i.reordered) AS prior_repeat_lines
            FROM order_products__prior i JOIN orders o USING(order_id) GROUP BY i.product_id)
        SELECT p.*,COALESCE(m.prior_product_lines,0) AS prior_product_lines,COALESCE(m.prior_buyers,0) AS prior_buyers,
        COALESCE(m.prior_repeat_lines,0) AS prior_repeat_lines,
        1.0*m.prior_repeat_lines/NULLIF(m.prior_product_lines,0) AS repeat_line_share
        FROM product_catalog p LEFT JOIN metrics m USING(product_id)''')
    # Build descriptive department totals from the same prior history.
    con.execute('''CREATE OR REPLACE TABLE department_history_metrics AS
        SELECT p.department_id,p.department,COUNT(*) AS prior_product_lines,SUM(i.reordered) AS prior_repeat_lines,
        COUNT(DISTINCT i.order_id) AS prior_orders,COUNT(DISTINCT o.user_id) AS prior_buyers,
        1.0*SUM(i.reordered)/COUNT(*) AS repeat_line_share
        FROM order_products__prior i JOIN product_catalog p USING(product_id) JOIN orders o USING(order_id) GROUP BY ALL''')
    # Only train users have a labelled final basket. Test baskets are unknown, never negatives.
    con.execute('''CREATE OR REPLACE TABLE evaluation_plan AS
        WITH last_prior AS (SELECT user_id,MAX(order_number) AS last_prior_number FROM orders WHERE eval_set='prior' GROUP BY user_id)
        SELECT t.user_id,v.order_id AS validation_order_id,v.order_number-1 AS validation_history_max_order_number,
               t.order_id AS final_target_order_id,t.order_number-1 AS final_history_max_order_number
        FROM orders t JOIN last_prior l USING(user_id)
        JOIN orders v ON v.user_id=t.user_id AND v.order_number=l.last_prior_number AND v.eval_set='prior'
        WHERE t.eval_set='train' ''')
    assert count('SELECT COUNT(*) FROM evaluation_plan')==count("SELECT COUNT(*) FROM orders WHERE eval_set='train'")
    # Create a small real-customer example for the lessons.
    con.execute('''CREATE OR REPLACE TABLE learning_order_items AS
        SELECT o.user_id,o.order_number,i.order_id,i.product_id,p.product_name,p.aisle,p.department,i.add_to_cart_order,i.reordered
        FROM order_products__prior i JOIN orders o USING(order_id) JOIN product_catalog p USING(product_id)
        WHERE o.user_id=1 AND o.order_number<=3 ORDER BY o.order_number,i.add_to_cart_order''')
    # Choose readable tables and small samples to export for analysis and learning.
    csvs={'products.csv':'SELECT * FROM product_catalog ORDER BY product_id',
          'product_history_metrics.csv':'SELECT * FROM product_history_metrics ORDER BY product_id',
          'department_history_metrics.csv':'SELECT * FROM department_history_metrics ORDER BY department_id',
          'evaluation_plan.csv':'SELECT * FROM evaluation_plan ORDER BY user_id',
          'learning_order_items.csv':'SELECT * FROM learning_order_items ORDER BY order_number,add_to_cart_order',
          'learning_orders.csv':'SELECT * FROM order_summary WHERE user_id=1 ORDER BY order_number',
          'order_summary_sample.csv':'SELECT * FROM order_summary ORDER BY order_id LIMIT 25'}
    # Write the chosen tables as CSVs, then save a compact order-summary Parquet file.
    for name,query in csvs.items():
        path=str(OUT/name).replace("'","''")
        con.execute(f"COPY ({query}) TO '{path}' (HEADER, DELIMITER ',')")
    con.execute(f"COPY order_summary TO '{str(OUT/'order_summary.parquet').replace(chr(39),chr(39)*2)}' (FORMAT PARQUET)")
    # Count the order groups and record known data limitations.
    split_counts={k:int(v) for k,v in con.execute('SELECT eval_set,COUNT(*) FROM orders GROUP BY eval_set').fetchall()}
    notes={
        'missing_product_names':count('SELECT COUNT(*) FROM products WHERE product_name IS NULL'),
        'products_in_missing_aisle_label':count("SELECT COUNT(*) FROM product_catalog WHERE aisle='missing'"),
        'products_in_missing_department_label':count("SELECT COUNT(*) FROM product_catalog WHERE department='missing'"),
        'first_orders_with_expected_blank_gap':count('SELECT COUNT(*) FROM orders WHERE order_number=1 AND days_since_prior_order IS NULL'),
        'gaps_recorded_as_30_or_more':count('SELECT COUNT(*) FROM orders WHERE days_since_prior_order=30'),
        'note':'30 is a capped value, not necessarily exactly 30 days. Weekday codes remain 0-6; no calendar dates or weekday-name mapping assumed.'
    }
    # Save a preparation summary; these checks are not recommendation scores.
    report={'status':'passed','source_counts':counts,'users':count('SELECT COUNT(DISTINCT user_id) FROM orders'),
            'order_splits':split_counts,'structural_checks':checks,'notes':notes,
            'known_product_lines':counts['order_products__prior']+counts['order_products__train'],
            'evaluation_users':count('SELECT COUNT(*) FROM evaluation_plan'),
            'decisions':['Source CSVs unchanged; no rows dropped or imputed.',
                'Prior orders are the history for descriptive metrics. Train final baskets are held back for later evaluation.',
                'Test order contents are unavailable and remain null, not zero or assumed empty.',
                'Validation uses each train user\'s last prior order; features must use earlier orders only.',
                'Global product/department history summaries use all prior orders; do not use them as validation features because they include validation targets.',
                'No recommendation algorithm, evaluation results or business findings generated in preparation.']}
    (AUDIT/'preparation_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    # Compact, independent reconciliations across table grains.
    assert count('SELECT SUM(product_lines) FROM order_summary')==report['known_product_lines']
    assert count('SELECT SUM(prior_product_lines) FROM product_history_metrics')==counts['order_products__prior']
    assert count('SELECT SUM(prior_repeat_lines) FROM product_history_metrics')==count('SELECT SUM(reordered) FROM order_products__prior')
    assert count('SELECT SUM(prior_product_lines) FROM department_history_metrics')==counts['order_products__prior']
    # Finish writing the database, close it and fingerprint the generated files.
    con.execute('CHECKPOINT')
    con.close()
    outputs={p.name:fingerprint(p) for p in OUT.iterdir() if p.is_file() and p.suffix in ['.csv','.parquet','.duckdb']}
    (AUDIT/'prepared_manifest.json').write_text(json.dumps(outputs,indent=2),encoding='utf-8')
    print(json.dumps({'status':'prepared','counts':counts,'users':report['users'],'evaluation_users':report['evaluation_users']},indent=2),flush=True)
    return report

# Run this section only when the file is launched directly.
if __name__=='__main__':prepare()
