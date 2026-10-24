# Project brief

## Status

Completed as a learning project and local prototype on 23 October 2026. The analysis, five-method comparison, selected weighted-recency rule, HTML prototype, exploratory pilot records and case study are documented. The first Version 2 timing experiment is closed without adoption. Portfolio presentation and public release are separate future work; stronger user testing and independent reproduction remain open.

## The question

How can I rank five Buy again suggestions to help returning grocery shoppers find familiar products?

This is an independent portfolio project using Instacart's historical public data, not client work or a feature commissioned by Instacart.

## The shopper and problem

Returning shoppers regularly buy some of the same groceries. They may have to search for those products each time they build a basket. A relevant shortlist could make familiar groceries more visible and easier to add.

The order data supports testing purchase predictions. It doesn't establish the searching problem, dietary restrictions or a reduction in shopping time. Customer research and prototype testing are still needed.

## Version 1: Buy again

- A visible Buy again area while a returning shopper builds a demo basket.
- Up to five unique products from that shopper's eligible purchase history, with readable names and factual reasons.
- Add a product or ignore it. Nothing is added automatically; ignoring isn't treated as dislike.
- Hide only the exact product ID and restore it later. Hiding Banana must not hide Bag of Organic Bananas.
- Save hidden products per example customer in this browser across visits. This isn't a real account or cross-device sync service.
- Apply hidden-product exclusions before selecting the top five. If fewer familiar candidates remain, show fewer rather than adding discovery products.
- Allow ordinary browsing/search in the demo. Keep a clearly labelled general-popularity fallback for missing history; new-customer outcomes aren't measured by this dataset.
- An interactive HTML prototype, saved analysis evidence and a portfolio case study. Method comparisons stay in the guide rather than the shopping UI. Example-user selection is a reviewer control, not a real shopper login flow.

The analysis compared popularity, personal frequency, weighted recency, logistic regression and boosted trees. Weighted recency is selected as the version-one default; the ML models remain documented comparison methods. The decision balances modest accuracy differences with explanation and maintenance needs.

**Outside Version 1:** new-product discovery, checkout extras, payments, live prices/stock, real customer accounts, Instacart integration, online retraining and a chatbot. A separate Power BI report isn't part of this project.

## What is built so far?

Data preparation, checks, three simple methods and two ML challengers are complete and validation-scored. History/basket groups, customer trade-offs, product coverage and a matched local runtime comparison are documented. Weighted recency is selected for version one. The final-evaluation procedure was fixed and predictions saved before answers. Final scoring is complete with checked frozen lists; weighted recency remains selected. The HTML prototype now uses saved real A/B examples with Add, Hide, Show again, search and Basket; C is simulated no-history. Case study and findings are written. Two exploratory timed sessions and basic owner layout/keyboard checks are recorded. Both participants tried search first, so the shorter second tasks don't establish a causal time saving. No formal comparative experiment or production release is claimed. The first Version 2 timing challenger has been prepared and development-tested; it did not meet the fixed adoption gate, so the current prototype remains unchanged.

## Completion and release checks

| Area | Ready when |
|---|---|
| Data | Source, table grain, joins and limitations are documented; required checks pass |
| Suggestions | At most five valid, unique products; explanations reflect the method; later answers never enter inputs |
| Controls | Add works; Hide affects only that exact product for the selected example user; restore makes it eligible again |
| Evaluation | Methods use the same customers and targets; scores, uncertainty, coverage and trade-offs are reported |
| Demo | A reviewer can use an example, inspect suggestions and find the performance explanation; errors are understandable |
| Handoff | Local setup instructions, walkthrough and limits are documented; independent setup reproduction remains a future release check |

Prototype success measures and research questions live in **Research and testing**. Numeric thresholds haven't been agreed; any targets set now won't be described as predating validation results we've already inspected.

## Version 2: purchase timing — first development test complete

**Question:** can recognising a familiar product's usual purchase gap improve next-basket suggestions over Version 1's weighted recency?

Version 1 asks how often and how recently the customer bought something. Version 2 tested one additional idea: whether a product tends to return after a certain number of shopping trips. This is a pattern in orders, not a claim about when food runs out. Quantity, household consumption and reasons for buying aren't available.

Start with **order gaps**, not exact calendar dates. Example: eggs appear in orders 2, 5 and 8, giving two gaps of three orders. Before predicting order 11, that pattern might be useful. It doesn't guarantee the shopper wants eggs. Products with too few repeats or irregular gaps may not have a reliable timing clue.

### Scope

- Keep the familiar-product candidate rule, up-to-five lists and exact-product Hide unchanged.
- Investigate typical gap, variation in gaps and orders passed since last purchase, calculated strictly from history before the target basket.
- A timing estimate needs at least three earlier purchases for two observed gaps; retain an explicit unavailable flag and a fallback for sparse histories. Two gaps are still limited evidence.
- For the next-order task, distinguish elapsed orders at the history cutoff from the expected gap to the next order (one order later). Never read target contents to construct the clue.
- Compare one agreed timing-aware challenger with the fixed five-order-half-life weighted-recency baseline on matching customers, candidates and baskets.
- Keep the current HTML prototype and Version 1 files unchanged while investigating. No new UI, discovery products, online learning or model complexity is assumed necessary.

### Available evaluation data

Metadata review found **75,000 customers outside the 131,209-person Version 1 comparison**, with no customer-ID overlap. Their official final test baskets still have unknown contents. We can instead target each customer's **last known prior basket** and use only the earlier orders as inputs. All 75,000 have at least two earlier orders available at that cutoff.

This is a newly separated retrospective customer cohort within the same public dataset. The source was already loaded and summarised during earlier preparation, so don't describe it as newly collected, entirely unseen data or a guaranteed pristine holdout. It tests a different cohort and earlier prediction point; Version 1's scores aren't directly comparable to its results. Assess the fixed Version 1 rule again on the same Version 2 targets as the challenger.

**Split created:** 60,000 development customers and 15,000 reserved audit customers, assigned by a fixed customer-ID hash rule before parsing target-product answers. Preparation produced 4,509,970 familiar-product candidates from earlier history. No target rows entered the feature table. The fixed protocol, source/code hashes and stage checks are saved in [the timing protocol](../05_Results/03_Checks/v2_timing_protocol.json) and [preparation report](../05_Results/03_Checks/v2_timing_preparation.json).

The first challenger gives the recency score up to a 50% bonus when repeated purchase gaps are consistent and the next order is close to that usual gap. Fewer observations and irregular gaps reduce the bonus. This was one prospectively fixed rule, not a settings search or a trained model.

### What would justify changing Version 1?

Use mean per-customer Recall@5 as the primary offline measure, with Precision@5, Hit Rate@5, paired uncertainty, short lists, timing availability and history-length groups alongside it. Precision still divides by five; recall includes the full target basket. Inspect gains and losses for individual customers and the added explanation/maintenance burden. Before Version 2 scoring, the implementation fixed an exploratory gate: at least +0.25 percentage points recall, a positive approximate paired 95% lower bound, precision no worse than -0.10 points and hit rate no worse than -0.25 points. These are assistant-selected project criteria under the implementation request, not business-agreed or industry-standard thresholds.

A timing challenger doesn't automatically become the new default. Keep weighted recency if the evidence doesn't justify a change. Any shopper-benefit claim still needs product testing beyond historical prediction accuracy.

### First development result

On the same 60,000 development customers, mean Recall@5 was **24.556% for weighted recency** and **24.581% for timing**: about **+0.025 percentage points**. The approximate paired 95% interval was **-0.003 to +0.052 points**. The gain was below the fixed 0.25-point criterion and the interval includes zero.

**Decision:** stop this fixed attempt and keep weighted recency. The reserved 15,000-person audit wasn't scored, and the shopping prototype wasn't changed. This doesn't establish that all timing approaches fail. Development answers are now inspected; any later attempt must disclose that reuse, retain the original result and leave the reserved audit for a genuinely fixed candidate. Don't quietly tune this attempt or claim the reserve is entirely new data. [Development evidence](../05_Results/03_Checks/v2_timing_development.json).

**Next:** review why a plausible new clue produced little gain, then decide whether a separate, explicitly planned experiment is worth doing. No repeated gap-basics quiz is needed.

## Version 3: product discovery — active extension

**Question:** can past purchases help rank unfamiliar products better than general popularity?

Justin authorised this extension after reviewing Version 1's exclusions. Version 1 and the stopped Version 2 timing experiment remain completed records. The earlier proposed “learn from use” version is deferred; Version 3 now means discovery.

### Small first scope

- A proposed separate “You might also like” section with up to three products. Keep Buy it again's five familiar products unchanged.
- “New” means absent from the customer's observed earlier orders, not necessarily never bought in their life.
- Baseline: rank products by their share of development history orders, exclude everything that shopper has already bought, then take three.
- Challenger to implement: score unfamiliar products through item-to-item similarity from development shoppers' earlier purchase histories. Similarity means products bought by overlapping shoppers, not proof of complementary use or dietary suitability. Fix similarity, minimum support, neighbour limits and fallback before scoring.
- Exclude already bought products in both methods. Never use target products to pick candidates. No prices, stock, checkout, accounts, click learning or automatic additions.

### Fair test and limits

Reuse the 60,000-person development cohort's earlier-only histories. These development answers were already inspected in V2; this is exploratory reuse, not a new untouched holdout. Leave the 15,000-person reserved audit unused during this stage. Any audit use needs a separately fixed discovery protocol and adoption criteria, not the timing experiment's failed gate or thresholds.

Compare both methods on the same targets and customer set. Proposed primary measure: Hit Rate@3 across all development customers, including those whose next basket contains no unfamiliar products. Also report mean Precision@3 (matches divided by three, even for short lists); Recall@3 among customers whose next basket contains at least one product absent from history (matches divided by that novel-product set); explicitly report that subgroup's size and the fraction with no novel products. Report coverage, short lists and paired uncertainty. Don't compare these scores directly with familiar-product Recall@5.

Products unseen anywhere in development history can't be recommended by this baseline; keep them in the novelty-recall denominator and report candidate coverage. Use development history only for shared statistics, never audit history or target contents. Because there are no shared calendar dates, this is a retrospective per-customer-order comparison, not a calendar-time production backtest. Shared historical statistics can still reflect cross-customer calendar ambiguity; disclose it.

A historical match doesn't show that recommendations caused exploration, sales or satisfaction. A later interface test would need discovery-specific tasks, not a request to click products already visible.

### Prepared so far

History-only popularity ranking is saved in `02_Data/02_Prepared/discovery_popularity.sqlite`: 47,352 products, based on 876,349 earlier orders and 8,838,134 product lines from 60,000 development shoppers. Preparation script: `03_Code/03_Model_Comparison/prepare_discovery_baseline.py`. Report: `05_Results/03_Checks/discovery_preparation.json`.

No personalised lists, similarity model, discovery accuracy scores or new UI have been built yet. Next implement and verify the unfamiliar-product filter and related-product comparison, then fix the scoring protocol before reading target answers for this task.

## How the work moves forward

Understand the problem → learn/check the data → compare methods → review trade-offs → build and test the demo → explain the evidence.

The Learning path is the checklist, Tasks holds work status, and the decision log records why choices change. Save a concise lesson/work summary at milestones, not after every question. This is solo work with AI help; no invented deadlines or research.

### Version 3: first discovery comparison complete

One fixed related-product method was compared with unfamiliar popularity on the same 60,000 development shoppers. Earlier-history links were binary: each shopper counts once per product when finding shared buyers. Similarity is shared buyers divided by the square root of the two product buyer counts. We required 50 buyers per product and five shared buyers, kept 40 neighbours per product, and used each shopper's ten highest recency-scored familiar products as seeds. Their recency scores weight the similarity contributions. Familiar products are excluded before taking three; unfamiliar popularity fills gaps. No settings search was run.

| Measure | Unfamiliar popularity | Related products |
|---|---:|---:|
| Hit Rate@3 — all 60,000 shoppers | 6.563% | 7.777% |
| Mean Precision@3 — all 60,000 shoppers | 2.296% | 2.766% |
| Mean novel-product Recall@3 — 49,118 shoppers with new products in the target basket | 1.816% | 2.197% |
| Distinct products suggested | 25 | 2,705 |

The hit-rate difference is **+1.213 percentage points**, approximately **+1.011 to +1.416 points** under a paired independent-customer calculation with the shared fitted statistics treated as fixed. It passed the exploratory gate fixed before this scoring run: at least +0.5 hit-rate points, a positive interval lower bound and no precision loss. These are agent-selected project criteria, not an industry or business standard. Passing warrants review, not automatic release.

There were 10,882 shoppers with no new products in their next basket; they remained in hit-rate and precision denominators. Of 259,492 novel target product lines, 259,071 appeared in the history-derived catalogue. Recall still includes unavailable products. Both methods filled all three slots; related products used 135 popularity-fill slots out of 180,000. Wider catalogue coverage isn't proof of better discovery or satisfaction.

This reuses development answers inspected during V2. It's an exploratory result, not fresh validation. There is no common-calendar backtest, and no causal shopper-benefit claim. Most customers still had no matching discovery suggestion. The 15,000 reserved customers remain unscored; V1's prototype and the portfolio site weren't changed.

Checks confirmed 360,000 total saved recommendations, no familiar-product suggestions, no audit customers, direct buyer-set checks for 100 product associations, saved-match checks for 100 shoppers per method and separate reranking checks for 100 random shoppers. Lists were saved and fingerprinted before this run read target products.

Evidence: [protocol](../05_Results/03_Checks/discovery_protocol.json), [development results](../05_Results/03_Checks/discovery_development.json), [independent verification](../05_Results/03_Checks/discovery_verification.json). Next: review this result together, then define a separate fixed audit plan if advancing. No further tuning or automatic audit run.

## Version 3: reserved discovery check — complete

23 October 2026. After reviewing development results, Justin authorised the reserved check. We wrote a separate audit protocol before reading its target products. We reused the exact development-fitted product relationships and popularity ranking; audit shoppers supplied only their own earlier history for personalisation. No model was refitted and no settings changed.

Both methods' 45,000 suggestions were saved and fingerprinted before opening audit product answers. The targets were the last known prior baskets for the fixed 15,000 reserved shoppers, not their unknown official final test baskets.

| Audit measure | Unfamiliar popularity | Related products |
|---|---:|---:|
| Hit Rate@3 — all 15,000 shoppers | 6.627% | 7.727% |
| Mean Precision@3 — all 15,000 shoppers | 2.351% | 2.738% |
| Mean novel-product Recall@3 — 12,253 shoppers with novel target products | 1.786% | 2.197% |
| Distinct suggested products | 25 | 1,444 |

The hit-rate gain was **1.100 percentage points**, with an approximate paired 95% interval of **+0.693 to +1.507 points**. Precision also improved. It passed the unchanged project gate: at least +0.5 hit-rate points, a positive interval lower bound and no precision loss. These are exploratory project criteria, not an industry standard or a business-benefit threshold.

Compared with popularity, 569 shoppers gained a hit, 404 lost a hit and 14,027 had the same hit/no-hit outcome: a net 165 more shoppers with at least one match. Same hit status doesn't imply identical products or match counts. Most shoppers still received no matching discovery product.

The 2,747 shoppers with no novel target products remained in hit-rate and precision denominators. Novel recall used the other 12,253 only. Of 63,830 novel target product lines, 63,728 appeared in the development-history catalogue; the unavailable products stayed in the recall denominator. All lists had three items. The related method used 18 popularity-fill slots out of 45,000.

Checks independently rebuilt rankings for 100 sampled shoppers before scoring, re-read source CSV answers and matches for 100 after scoring, and verified all recommendations excluded personal history and used the exact audit cohort. Model, code, protocol, source-history and prediction fingerprints remained unchanged. No V1/V2 model or shopping UI was changed.

**Conclusion:** the related-product method beat unfamiliar popularity in both development and this reserved retrospective check. That supports a discovery prototype experiment; it doesn't establish that recommendations cause purchases, satisfaction or useful exploration. Shared historical data lacks common calendar dates, the source had previously been loaded/summarised, and the interval assumes independent shoppers conditional on the frozen shared statistics. Don't describe this as new live data or perfectly pristine original-source validation.

**The audit is now exposed.** Don't tune against it or call a rerun a fresh test. V2 timing remains stopped and was never audit-scored; this was a separately authorised discovery check. Next: discuss a separate “You might also like” prototype section and discovery-specific user tasks. No discovery UI has been built or released yet.

Evidence: [audit protocol](../05_Results/03_Checks/discovery_audit_protocol.json), [saved-prediction checks](../05_Results/03_Checks/discovery_audit_preparation.json), [audit results](../05_Results/03_Checks/discovery_audit.json).

## Discovery prototype added — 23 October 2026

Justin authorised the UI extension after the reserved check. The local shopping page now has a separate “You might also like” row between Buy it again and Browse, using up to three unfamiliar items from the unchanged discovery method. Existing A/B histories personalise the saved development-fitted relationships; no target baskets are read or models refitted for the export. These are illustrative V1 example shoppers, not the audit sample.

A: Trail Mix, Clementines, Crunchy Oats 'n Honey Granola Bars. B: Trail Mix, Soda, Clementines. C retains its popular section with no duplicate discovery row. Add/toggle/remove use the existing basket. Familiar-item Hide remains unchanged; discovery doesn't have Hide in this first UI iteration. New products use neutral placeholders unless an embedded photo already exists. Source names are retained; display categories are simplified.

The original V1 study URLs suppress discovery and retain their original browse/search catalogue. CSS, old photos, Buy again data and hidden-item storage keys are unchanged. The pre-discovery HTML is archived at 99_Archive/02_Prototype_Revisions/buy_again_before_discovery.html. Claude's portfolio site/copy wasn't edited.

Checks passed in a Node VM with a stub DOM: A/B exclusions, Add/toggle/remove event handlers, search, familiar Hide separation, C, loading/error suppression and original study conditions. This isn't browser visual review, accessibility certification or user testing. Export/check reports: 05_Results/03_Checks/discovery_demo_export.json and discovery_prototype_checks.json. Exporter: 03_Code/05_Prototype/export_discovery_shoppers.py. Next: review the actual page, then test whether the new row is understandable and useful; no further model tuning on exposed audit answers.

## Current UI: five discovery products — 24 October 2026

Justin requested five discovery cards. The illustrative A/B export now takes the top five from the unchanged similarity ranking; each has five unfamiliar products, all from related-product scoring, with no popularity-fill slots. C retains its popular fallback. All new cards have embedded illustrative photos, including Pub Mix and Apples. Add/remove and original study suppression passed stub-DOM checks. No browser visual review or discovery user study is claimed.

**Evidence boundary:** original development and reserved metrics remain @3. The five-card presentation is a subsequent UI scope change, not a newly validated @5 method. No evaluation scripts, frozen models, protocols or scores were changed or rerun. Audit answers remain exposed; don't imply a fresh five-item audit. Claude's portfolio copy is unchanged.

A: Trail Mix, Clementines, Crunchy Oats 'n Honey Granola Bars, Pub Mix, Apples. B: Trail Mix, Soda, Clementines, Crunchy Oats 'n Honey Granola Bars, Zero Calorie Cola. Three of five overlap. See the Learning notes for the traced explanation and limitations.
