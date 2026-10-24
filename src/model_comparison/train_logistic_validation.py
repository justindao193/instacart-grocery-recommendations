"""Shared validation runner: logistic by default, or one fixed boosted-tree challenger."""
import heapq
import json
import math
from pathlib import Path
import sqlite3
import time
import warnings
import pickle
import hashlib
import joblib

import numpy as np
import pandas as pd
import sklearn
from scipy.special import expit
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import HistGradientBoostingClassifier
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[2]
FEATURES = ['purchase_orders','purchase_share','orders_since_last_purchase',
            'recency_score','history_orders']
SETTINGS = {'C':1.0,'solver':'lbfgs','max_iter':500,'tol':1e-6,
            'class_weight':None,'random_state':0}
TREE_SETTINGS = {'learning_rate':0.1,'max_iter':100,'max_leaf_nodes':15,
                 'max_depth':4,'min_samples_leaf':100,'l2_regularization':1.0,
                 'early_stopping':False,'random_state':0,'class_weight':None}


def announce(message):
    print(message,flush=True)


def load_saved_logistic(outputs, checks):
    """Restore the original fitted scaler and weights without fitting again."""
    state = json.loads((outputs/'logistic_model.json').read_text(encoding='utf-8'))
    report = json.loads((checks/'logistic_validation.json').read_text(encoding='utf-8'))
    assert state['features']==FEATURES and report['status']=='passed'
    assert state['sklearn_version']==sklearn.__version__
    scaler = StandardScaler()
    scaler.mean_ = np.asarray(state['mean'],dtype=np.float64)
    scaler.scale_ = np.asarray(state['scale'],dtype=np.float64)
    scaler.var_ = scaler.scale_**2
    scaler.n_features_in_ = len(FEATURES)
    scaler.n_samples_seen_ = report['training_rows']
    classifier = LogisticRegression(**state['settings'])
    classifier.coef_ = np.asarray([state['coefficients']],dtype=np.float64)
    classifier.intercept_ = np.asarray([state['intercept']],dtype=np.float64)
    classifier.classes_ = np.asarray([0,1])
    classifier.n_features_in_ = len(FEATURES)
    classifier.n_iter_ = np.asarray([report['iterations']])
    return make_pipeline(scaler,classifier), state


def run(kind='logistic'):
    assert kind in ('logistic','boosted_trees')
    is_logistic = kind=='logistic'
    settings = SETTINGS if is_logistic else TREE_SETTINGS
    method_name = 'logistic_regression' if is_logistic else 'boosted_trees'
    # Fix this first attempt before viewing its scores; no parameter search or final targets.
    checks = ROOT/'05_Results/03_Checks'
    output = ROOT/'02_Data/03_Model_Outputs'
    report_path = checks/f'{kind}_validation.json'
    spec = {'status':'started','stage':'validation only','features':FEATURES,
            'settings':settings,'scaling':'StandardScaler fitted on training only' if is_logistic else 'No scaling needed for these tree splits; raw prepared inputs',
            'regularisation':'L2' if is_logistic else 'Small trees, minimum leaf size and L2',
            'sampling':'all prepared training rows; no negative sampling',
            'row_weighting':'equal customer-product row weights; customers have differing candidate counts',
            'tie_break':'score descending, last purchase order descending, product_id ascending',
            'parameter_search':False,'final_baskets_scored':False}
    if not is_logistic:
        spec['working_recall_gain_target_pp'] = 0.5
        spec['target_note'] = 'Proposed experiment target before this result, not an industry rule or final business acceptance criterion.'
        spec['early_stopping_note'] = 'Fixed 100 rounds; no automatic random-row validation split and no external validation answers during fit.'
    prep = json.loads((checks/'ml_feature_preparation.json').read_text(encoding='utf-8'))
    assert prep['status']=='passed' and prep['feature_columns']==FEATURES
    report_path.write_text(json.dumps(spec,indent=2),encoding='utf-8')
    database = ROOT/'02_Data/02_Prepared/instacart_ml.sqlite'
    with sqlite3.connect(database.as_uri()+'?mode=ro',uri=True) as con, threadpool_limits(limits=2):
        assert con.execute("SELECT value FROM build_metadata WHERE key='features_checked'").fetchone()==('passed',)
        # Load only the declared five inputs and training labels, never identifiers or answers as inputs.
        announce('Reading the checked training inputs...')
        training = pd.read_sql_query('SELECT '+','.join(FEATURES)+",bought_next FROM ml_features WHERE stage='training'",con)
        X = training[FEATURES].to_numpy(dtype=np.float64)
        y = training['bought_next'].to_numpy(dtype=np.int8)
        del training
        assert np.isfinite(X).all() and set(np.unique(y))=={0,1}
        expected_rows = next(r['rows'] for r in prep['stages'] if r['stage']=='training')
        assert len(X)==expected_rows
        model = make_pipeline(StandardScaler(),LogisticRegression(**settings)) if is_logistic else HistGradientBoostingClassifier(**settings)
        # Learn only from training rows; unresolved logistic convergence warnings stop scoring.
        announce(f'Fitting {method_name} on {len(X):,} training rows...')
        started = time.perf_counter()
        with warnings.catch_warnings():
            warnings.simplefilter('error',ConvergenceWarning)
            model.fit(X,y)
        fit_seconds = time.perf_counter()-started
        sample_X = X[:100].copy()
        if is_logistic:
            scaler,clf = model.steps[0][1],model.steps[1][1]
            assert scaler.n_samples_seen_==len(X)
            assert np.allclose(scaler.mean_,X.mean(axis=0),rtol=1e-10,atol=1e-10)
            assert np.isfinite(clf.coef_).all() and np.isfinite(clf.intercept_).all()
            mean_before,scale_before = scaler.mean_.copy(),scaler.scale_.copy()
            # Check that a portable saved-weight calculation matches the library on known rows.
            portable = expit(((X[:100]-scaler.mean_)/scaler.scale_) @ clf.coef_[0]+clf.intercept_[0])
            assert np.allclose(portable,model.predict_proba(X[:100])[:,1],atol=1e-12)
        else:
            assert model.n_iter_==settings['max_iter'] and not model.do_early_stopping_
        fitted_digest = hashlib.sha256(pickle.dumps(model)).hexdigest()
        train_rows = len(X)
        del X,y

        # Count complete actual baskets, including products that were not rebuy candidates.
        actual = dict(con.execute('''SELECT e.user_id,COUNT(*) FROM evaluation_plan e
            JOIN order_products__prior i ON i.order_id=e.validation_order_id GROUP BY e.user_id'''))
        cutoffs = dict(con.execute('SELECT user_id,validation_history_max_order_number FROM evaluation_plan'))
        targets = dict(con.execute('SELECT user_id,validation_order_id FROM evaluation_plan'))
        out_path = output/f'{kind}_validation.sqlite'
        with sqlite3.connect(out_path) as out:
            out.executescript('''DROP TABLE IF EXISTS recommendations; DROP TABLE IF EXISTS scores;
                CREATE TABLE recommendations(user_id INTEGER,product_id INTEGER,rank INTEGER,
                    score REAL,bought_next INTEGER,PRIMARY KEY(user_id,rank),UNIQUE(user_id,product_id));
                CREATE TABLE scores(user_id INTEGER PRIMARY KEY,validation_order_id INTEGER,
                    actual_products INTEGER,matched_products INTEGER,precision_at_5 REAL,
                    recall_at_5 REAL,hit_at_5 INTEGER,history_orders INTEGER);''')
            user_scores,rec_batch,score_batch = {},[],[]
            current,heap,candidates = None,[],0
            short_lists = 0
            def finish_user():
                nonlocal short_lists
                if current is None:
                    return
                chosen = sorted(heap,reverse=True)
                assert len(chosen)==min(5,candidates)
                hits = sum(item[3] for item in chosen)
                size = actual[current]
                assert 0<=hits<=min(5,size)
                metrics = (hits/5,hits/size,int(hits>0))
                user_scores[current] = metrics
                short_lists += len(chosen)<5
                rec_batch.extend((current,-item[2],rank,item[0],item[3])
                                 for rank,item in enumerate(chosen,1))
                score_batch.append((current,targets[current],size,hits,*metrics,cutoffs[current]))
                if len(score_batch)>=5000:
                    out.executemany('INSERT INTO recommendations VALUES (?,?,?,?,?)',rec_batch)
                    out.executemany('INSERT INTO scores VALUES (?,?,?,?,?,?,?,?)',score_batch)
                    rec_batch.clear()
                    score_batch.clear()
            # Score in chunks and retain only five per customer; the scaler is never refitted.
            announce('Training finished. Scoring validation candidates in chunks...')
            started = time.perf_counter()
            seen = 0
            query = 'SELECT user_id,product_id,last_purchase_order,bought_next,'+','.join(FEATURES)+" FROM ml_features WHERE stage='validation' ORDER BY user_id,product_id"
            for chunk in pd.read_sql_query(query,con,chunksize=200_000):
                values = chunk[FEATURES].to_numpy(dtype=np.float64)
                probabilities = model.predict_proba(values)[:,1]
                assert np.isfinite(probabilities).all() and ((probabilities>=0)&(probabilities<=1)).all()
                keys = chunk[['user_id','product_id','last_purchase_order','bought_next']].to_numpy(dtype=np.int64)
                for (uid,pid,last,label),probability in zip(keys,probabilities):
                    uid,pid,last,label = int(uid),int(pid),int(last),int(label)
                    if uid!=current:
                        finish_user()
                        current,heap,candidates = uid,[],0
                    candidates += 1
                    item = (float(probability),last,-pid,label)
                    if len(heap)<5:
                        heapq.heappush(heap,item)
                    elif item>heap[0]:
                        heapq.heapreplace(heap,item)
                seen += len(chunk)
            finish_user()
            out.executemany('INSERT INTO recommendations VALUES (?,?,?,?,?)',rec_batch)
            out.executemany('INSERT INTO scores VALUES (?,?,?,?,?,?,?,?)',score_batch)
            out.commit()
            scoring_seconds = time.perf_counter()-started
            assert seen==next(r['rows'] for r in prep['stages'] if r['stage']=='validation')
            assert set(user_scores)==set(actual) and len(user_scores)==131209
            assert short_lists==3521
            if is_logistic:
                assert np.array_equal(scaler.mean_,mean_before) and np.array_equal(scaler.scale_,scale_before)
                assert scaler.n_samples_seen_==train_rows
            assert hashlib.sha256(pickle.dumps(model)).hexdigest()==fitted_digest
            # Independently sort complete candidate lists and recompute overlaps for 100 users.
            for uid in sorted(user_scores)[:100]:
                frame = pd.read_sql_query('SELECT product_id,last_purchase_order,bought_next,'+','.join(FEATURES)+" FROM ml_features WHERE stage='validation' AND user_id=?",con,params=[uid])
                frame['score'] = model.predict_proba(frame[FEATURES].to_numpy(dtype=np.float64))[:,1]
                expected = frame.sort_values(['score','last_purchase_order','product_id'],ascending=[False,False,True]).head(5)
                saved = out.execute('SELECT product_id FROM recommendations WHERE user_id=? ORDER BY rank',[uid]).fetchall()
                assert [r[0] for r in saved]==expected.product_id.tolist()
                assert int(expected.bought_next.sum())==out.execute('SELECT matched_products FROM scores WHERE user_id=?',[uid]).fetchone()[0]

        # Compare per-customer scores on identical complete baskets against weighted recency.
        announce('Checking the paired comparison with weighted recency...')
        baseline = con.execute('''WITH ranked AS (
            SELECT user_id,bought_next,ROW_NUMBER() OVER (PARTITION BY user_id
                ORDER BY recency_score DESC,last_purchase_order DESC,product_id) AS rank
            FROM ml_features WHERE stage='validation')
            SELECT user_id,SUM(bought_next) FROM ranked WHERE rank<=5 GROUP BY user_id''').fetchall()
        assert {r[0] for r in baseline}==set(user_scores)
        ids = sorted(user_scores)
        baseline_hits = dict(baseline)
        ml = np.array([user_scores[uid] for uid in ids],dtype=np.float64)
        reference = np.array([(baseline_hits[uid]/5,baseline_hits[uid]/actual[uid],int(baseline_hits[uid]>0)) for uid in ids])
        saved = json.loads((checks/'weighted_recency_validation.json').read_text(encoding='utf-8'))
        comparison = {}
        for col,metric in enumerate(['precision_at_5','recall_at_5','hit_at_5']):
            assert abs(reference[:,col].mean()-saved['comparison'][metric]['weighted_recency'])<1e-10
            diff = ml[:,col]-reference[:,col]
            margin = 1.96*diff.std(ddof=1)/math.sqrt(len(diff))
            comparison[metric] = {method_name:float(ml[:,col].mean()),
                'weighted_recency':float(reference[:,col].mean()),
                'difference_percentage_points':float(diff.mean()*100),
                'paired_approx_95pct_interval_pp':[float((diff.mean()-margin)*100),float((diff.mean()+margin)*100)]}
        groups = []
        for label,low,high in [('1-5',1,5),('6-15',6,15),('16+',16,1000000)]:
            mask = np.array([low<=cutoffs[uid]<=high for uid in ids])
            groups.append({'history_orders':label,'customers':int(mask.sum()),
                f'{kind}_recall':float(ml[mask,1].mean()),'recency_recall':float(reference[mask,1].mean())})

        # Align saved logistic scores by customer, target basket and full basket size as well.
        logistic_comparison = None
        if not is_logistic:
            with sqlite3.connect((output/'logistic_validation.sqlite').as_uri()+'?mode=ro',uri=True) as previous:
                old = previous.execute('''SELECT user_id,validation_order_id,actual_products,
                    precision_at_5,recall_at_5,hit_at_5 FROM scores ORDER BY user_id''').fetchall()
            assert [row[0] for row in old]==ids
            assert all(row[1]==targets[row[0]] and row[2]==actual[row[0]] for row in old)
            logistic_scores = np.array([row[3:] for row in old],dtype=np.float64)
            logistic_comparison = {}
            for col,metric in enumerate(['precision_at_5','recall_at_5','hit_at_5']):
                diff = ml[:,col]-logistic_scores[:,col]
                margin = 1.96*diff.std(ddof=1)/math.sqrt(len(diff))
                logistic_comparison[metric] = {'logistic_regression':float(logistic_scores[:,col].mean()),
                    'boosted_trees':float(ml[:,col].mean()),'difference_percentage_points':float(diff.mean()*100),
                    'paired_approx_95pct_interval_pp':[float((diff.mean()-margin)*100),float((diff.mean()+margin)*100)]}

        # Save transparent weights/rulers, runtime checks and scores; no final winner is declared.
        if is_logistic:
            model_state = {'features':FEATURES,'mean':scaler.mean_.tolist(),'scale':scaler.scale_.tolist(),
                'coefficients':clf.coef_[0].tolist(),'intercept':float(clf.intercept_[0]),
                'settings':settings,'sklearn_version':sklearn.__version__,
                'formula':'sigmoid(sum((x-mean)/scale * coefficients) + intercept)',
                'warning':'Scores are not calibrated or causal effects; weights use correlated inputs.'}
            (output/'logistic_model.json').write_text(json.dumps(model_state,indent=2),encoding='utf-8')
        else:
            # Reload only this locally created model, never an untrusted pickle from outside.
            model_path = output/'boosted_trees_model.joblib'
            joblib.dump(model,model_path)
            restored = joblib.load(model_path)
            assert np.allclose(restored.predict_proba(sample_X),model.predict_proba(sample_X),atol=1e-12)
        spec.update({'status':'passed','sklearn_version':sklearn.__version__,
            'training_rows':train_rows,'validation_candidate_rows':seen,'customers':len(ids),
            'short_lists':short_lists,'comparison':comparison,'history_groups':groups,
            'training_completed':True,'iterations':int(clf.n_iter_[0]) if is_logistic else int(model.n_iter_),'fit_seconds':fit_seconds,
            'validation_scoring_seconds':scoring_seconds,
            'timing_note':'One local batch run including SQLite/chunk/ranking work; not app response latency.',
            'checks':{'training_inputs_only':True,'fitted_model_unchanged_after_validation':True,
                'independent_top5_users':100,'saved_model_predictions_match':True,
                'same_cohort_and_baskets':True,'baseline_saved_scores_match':True},
            'limits':'Exploratory validation; final targets untouched. One training target per known customer. '
                'Candidate rows weighted equally, not customers. No calibration or live benefit test.'})
        if is_logistic:
            spec['standardised_weights'] = dict(zip(FEATURES,clf.coef_[0].tolist()))
        else:
            spec['comparison_with_logistic'] = logistic_comparison
            spec['meets_working_recall_gain_target'] = comparison['recall_at_5']['difference_percentage_points']>=0.5
        report_path.write_text(json.dumps(spec,indent=2),encoding='utf-8')
    announce(f'{method_name} fitted and validation checks passed. Final baskets untouched.')
    announce(json.dumps(comparison,indent=2))


if __name__=='__main__':
    run()
