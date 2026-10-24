# Decision log

| Date | Decision | Why | Status |
|---|---|---|---|
| 2026-10-20 | Use the Instacart order dataset | A recognisable company release with linked order and product history | Chosen |
| 2026-10-20 | Focus on next-basket recommendations | The records support purchased baskets, not browsing abandonment | Chosen |
| 2026-10-20 | Retrieve the CSVs from a documented archive | The original download isn't accessible; check archive hashes and disclose the retrieval route | Documented |
| 2026-10-20 | Keep train final baskets out of history | They provide a later answer to check against | Implemented in validation; final check pending |
| 2026-10-20 | Use the last prior basket for earlier validation | Try ideas without tuning against the final answer | Implemented in validation; final check pending |
| 2026-10-20 | Keep unknown test contents blank | Missing labels aren't empty baskets | Chosen |
| 2026-10-20 | Write findings together after discussing the evidence | I want to understand and explain the analysis first | Chosen |

Current choice: weighted recency is the version-one default, selected on 22 October 2026 after validation comparisons. The iteration record below explains why. Final evaluation and the app are still pending.


## Milestone review template


- Date and milestone: [To fill]
- What was completed, with a file or result: [To fill]
- What was learned: [To fill]
- Decision and alternatives considered: [To fill]
- Why this choice is reasonable: [To fill]
- What changed in scope or priority: [To fill]
- Current blocker or risk: [To fill]
- Next useful task: [To fill]



The current scope is in Project brief; lesson history is in Learning log. Use this file for decisions and their reasons rather than repeating the whole plan.


## 22 October 2026 — First ML training split

Agreed with Justin: start with one training target per eligible customer, immediately before their existing validation basket. For validation order v, use order v-1 as the training target and orders up to v-2 as training inputs. Require at least one earlier input order (v >= 3). Validation features still end at v-1; final official train baskets remain untouched. This tests later purchases for known customers, not generalisation to entirely new customers.

Read every row of the saved evaluation_plan.csv: all 131,209 evaluation customers have validation_history_max_order_number >= 2 and meet this minimum history rule. This checks split eligibility only; no feature table, labels, model fit or final scoring was executed. Before fitting, verify training-target contents and candidate/feature cutoffs, and apply the same cutoff to any population-level features.


## 22 October 2026 — Use SQLite for current ML preparation

Justin approved Python/SQLite to continue locally while Smart App Control blocks DuckDB. No Windows policy change or dependency downgrade. Existing source data, DuckDB database/scripts and saved outputs remain. The SQLite feature preparation passed runtime checks and reproduced both existing personal methods' aggregate validation metrics. This validates the preparation path, not a trained ML model or customer benefit. Details: 03_Code/03_Model_Comparison/build_ml_features.py and 05_Results/03_Checks/ml_feature_preparation.json.


## 22 October 2026 — Choose weighted recency for version one

**Decision:** I chose weighted recency as the default Buy again method for the first demo. Logistic regression and boosted trees stay in the analysis and planned comparison view. This is a product trade-off made before final evaluation, not a claim that weighted recency has the highest prediction score.

### How I iterated

1. **Start with general popularity.** I needed a simple reference: give everyone the same five popular products. It established a baseline, but ignored individual shopping history.
2. **Use personal frequency.** I counted earlier orders containing each customer's familiar products. This gave a much stronger result. Recency broke ties, followed by product ID.
3. **Give recent purchases more weight.** I tested one fixed five-order half-life. Older purchases still contributed, but counted less. This improved recall over personal frequency without introducing a fitted ML model.
4. **Test logistic regression.** I used five purchase-history clues and a training-only scaler so the model could learn their weights. The first fixed attempt performed almost the same as weighted recency, giving no clear practical advantage.
5. **Test boosted trees.** I used the same five inputs and baskets with 100 small trees to allow more flexible combinations. The model improved prediction slightly, but the recall gain was below the proposed working target.

| Tested approach | Mean validation Recall@5 |
|---|---:|
| General popularity | 4.714% |
| Personal frequency | 23.441% |
| Weighted recency | 24.543% |
| Logistic regression | 24.546% |
| Boosted trees | 24.707% |

Same **131,209 customers and validation baskets** for all five. Recall is matches / actual basket products, calculated per customer and then averaged. General popularity can include unfamiliar products; the other methods are restricted to eligible personal history. I tested these five approaches, not every possible recommendation algorithm or parameter setting.

### Why I chose the weighted rule

- **Strong enough to be a useful first-version candidate.** It beat the general and personal-frequency baselines. This is a relative validation comparison, not proof of real shopper benefit.
- **The ML gain was modest.** Trees added about +0.164 percentage points recall. The approximate paired interval was +0.136 to +0.192 points under independent-customer assumptions, so I acknowledge the measured gain rather than call the models identical. It was below the proposed +0.5-point working experiment target, introduced before the tree result but after earlier validation work. That target isn't an industry rule or a pre-registered business success criterion.
- **The broader checks didn't show a large coverage advantage.** Trees suggested 29,271 different products versus 29,138 for weighted recency, with slightly less top-ten concentration. All three personal variants had the same 3,521 short lists. The tree gave more matches to 6,794 customers, the same match count to 119,054 and fewer to 5,361.
- **Speed wasn't the reason to reject trees.** All three personal methods were fast in the matched local prepared-input test. Model-only medians were about 0.005 ms for weighted ranking, 0.204 ms for logistic scaling/scoring/ranking and 0.541 ms for trees. Those aren't full app response times, and fetching saved lists was nearly identical.
- **The simpler method fits the first demo.** I can trace each past purchase's contribution, explain the five-order rule and maintain it without a separate fitted model/scaler. It still needs reliable data and checks. I judged the small extra gain insufficient to make trees the default for this version.

The useful outcome wasn't getting machine learning to win. It was testing whether the added complexity earned its place and making the trade-off explicit. The ML experiments remain part of the portfolio evidence.

### Rule selected before final evaluation

Use only eligible earlier purchases. For each customer-product pair, sum `0.5 ** ((history_cutoff_order - purchase_order_number) / 5)`, rounded to 12 decimals. Rank by score descending, latest purchase order descending, then product ID ascending. Choose up to five distinct familiar products. Keep short lists rather than add unfamiliar filler. The demo will apply exact-product Hide exclusions before selecting its five; those controls aren't built yet.

No new parameter search is planned for this version. The exact final-evaluation execution and reporting procedure must be written down before reading final basket answers. Official train baskets remain the untouched final targets. No final scores, deployed app, live customer experiment, time savings or revenue impact are claimed.

Evidence: validation reports, logistic comparison, tree comparison, customer trade-offs, coverage, [runtime](../results/prediction_runtime.json) and basket-size review.

This is an AI-assisted portfolio learning project. AI helped with code preparation, checking and explanations; I worked through the evidence and chose the first-version direction. This record doesn't claim independent mastery of every implementation detail.



## 22 October 2026 — Fix final-evaluation procedure before execution

Documented the procedure in [Data and methods](data_and_methods.md) after version-one selection and before final prediction/scoring. Same131209users; all allowed prior history at final cutoffs; unchanged methods and frozen original ML models/scaler with no refit. Save and check prediction lists before reading final product answers. Primary mean Recall@5, supporting metrics, paired differences/approximate intervals and existing groups/coverage definitions. If evidence is weak, report it rather than tune against final answers. Final features and execution still need implementation; no final score is claimed.


## 22 October 2026 — Complete the fixed final check without changing selection

After Justin explicitly asked to score, verified frozen prediction/model/source/code/plan hashes, opened final product answers and scored the saved lists. No refit/regeneration and unchanged prediction bytes. Weighted recency remains the choice made before final results. Final mean Recall@5:frequency23.116%,weighted24.276%,logistic24.279%,trees24.452%;popularity4.687%. Weighted gain over frequency+1.160pp; trees retain a modest gain over weighted. This is a later sequence check, not measured customer value. Full checks and paired/group reports in [final_evaluation.json](../results/final_evaluation.json).

The final holdout is now inspected and cannot be reused for tuning or presented as fresh after a new method change. No new model-selection decision was made from these scores. App and business findings remain ahead.


## 23 October 2026 — Stop the first V2 timing attempt at development

Under Justin's instruction to implement Version2, fixed one timing-bonus formula, 60,000/15,000 customer split and prospective gates before parsing new target answers. The development recall gain was+0.0249 percentage points, below0.25, with an approximate paired interval spanning zero. Retain the result rather than change the threshold or tune constants after seeing it. Audit entry point refuses this failed candidate;15,000 reserved customers weren't scored. Keep Version1's prototype and selected rule unchanged. Any further timing experiment requires a separate disclosed plan and must acknowledge inspected development answers. This is an implementation-stage stopping decision under the recorded rule, not a claim that Justin reviewed the new result yet. Evidence:v2_timing_protocol.json and v2_timing_development.json in03_Checks.

## 23 October 2026 — Close the learning-project scope

Following the completion discussion, Justin asked to update the learning records and related material. Retain weighted recency and close the first V2 timing attempt without adoption or audit scoring. Complete the case-study record with that outcome. The delivered scope is checked analysis plus a local prototype and exploratory pilot evidence, not a production service or proven shopping-time improvement. Further tuning, controlled research, portfolio presentation and publishing are separate decisions.

## 23 October 2026 — Start Version 3 discovery

Justin authorised a separate discovery experiment: up to three unfamiliar suggestions, with popularity compared against a related-product approach. Keep Buy again unchanged. “New” refers to recorded history only. Reuse exposed development data honestly; reserve audit remains unused. Scope and preparation are recorded, but there is no adoption decision or discovery result yet.

## 23 October 2026 — First discovery challenger passes exploratory development gate

Fixed one co-buyer similarity method before discovery scoring: 50-buyer product support, five shared buyers, 40 neighbours, ten recency-weighted personal seeds and unfamiliar-popularity fallback. Saved both methods' three-product lists before reading development answers for this task. Hit rate 6.563% baseline versus 7.777% related; +1.213 points, approximate paired interval +1.011 to +1.416. Precision also improved. Agent-selected +0.5-point gate passed, but development answers were previously exposed in V2. No claim of Justin reviewing or choosing this method yet. Next review the result together; any reserved audit needs a separate fixed plan. No UI or portfolio changes.

## 23 October 2026 — Discovery clears the fixed reserved-check criteria

Justin authorised the check after development review. Retained the exact models/settings and +0.5pp hit-gain/positive interval/no precision-loss gate in a separate pre-answer protocol. Reserved hit gain+1.100pp with interval+.693 to+1.507, precision also higher: gate passed. Recommendation is to consider a small discovery prototype, not claim proven benefit or automatic deployment. No claim Justin has already selected or user-tested the discovery UI. The audit is now exposed and cannot support post-result tuning as fresh validation. V2 timing wasn't reopened.

## 23 October 2026 — Authorised discovery prototype

Justin approved adding the separate section. Reused the fixed method with existing illustrative A/B histories; preserved C fallback and V1 study conditions. Discovery initially supports Add/remove only, with no new Hide controls. No claims of tested customer benefit, no model changes and no portfolio deployment. Visual review and discovery user testing remain next.

## 24 October 2026 — Five-item presentation, preserve three-item evidence

Justin requested five discovery suggestions. Extended only A/B's illustrative UI lists, leaving the fixed discovery method and original @3 evaluation evidence intact. No replacement accuracy claims. Similar A/B recommendations traced to overlapping shared-buyer product links; don't manually force different products for appearance. B's one-product history is a documented personalisation limitation. No new UI study or deployment.
