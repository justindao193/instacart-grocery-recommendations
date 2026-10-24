# Findings

These observations use the saved final evaluation, not a new model run. All methods share 131,209 customers and final target baskets. I selected weighted recency before scoring these answers.

## 1. Personal history was more useful than one list for everyone

Weighted recency reached 24.276% mean Recall@5, compared with 4.687% for general popularity: +19.589 percentage points. Hit rate was 79.375% versus 36.242%. This supports using personal history to predict later baskets in this cohort. It doesn't prove that shoppers want the feature or that it saves time. Popularity could choose unfamiliar products, while weighted recency was limited to familiar ones.

## 2. Recency improved on frequency, but not for everyone

Weighted recency reached 24.276% mean recall versus 23.116% for personal frequency. The paired difference was +1.160 percentage points, with an approximate 95% interval of +1.112 to +1.208 under independent-customer assumptions.

Compared with frequency, 19,217 customers got more matching products, 102,489 got the same count and 9,503 got fewer. The average improvement doesn't mean every shopper benefited. Equal match counts don't necessarily mean identical lists.

## 3. The ML gain was small enough to require a product trade-off

Boosted trees reached 24.452% mean recall versus 24.276% for weighted recency: +0.176 percentage points, with an approximate paired 95% interval of +0.148 to +0.205. Logistic regression reached 24.279%; its +0.0027-point recall difference from weighted recency had an interval spanning zero. These are results for the tested fixed attempts, not proof that all ML methods behave the same.

I kept weighted recency for its explanation and maintenance advantages, accepting lower accuracy. All approaches were fast in the local prepared-input test; speed wasn't the deciding objection to trees.

## Final comparison

| Method | Mean Precision@5 | Mean Recall@5 | Hit Rate@5 |
|---|---:|---:|---:|
| General popularity | 9.48% | 4.69% | 36.24% |
| Personal frequency | 35.41% | 23.12% | 78.23% |
| Weighted recency — selected | 37.32% | 24.28% | 79.37% |
| Logistic regression | 37.30% | 24.28% | 79.38% |
| Boosted trees | 37.58% | 24.45% | 79.45% |

For each customer, precision = matches / 5, even if a list has fewer products. Recall = matches / all distinct products in the actual target basket, averaged across customers. Hit rate = customers with a match / 131,209. Final target baskets contained 1,384,617 product lines. Each personal method produced 651,660 suggestions; 2,168 customers had fewer than five familiar candidates. The popularity method filled all 656,045 slots.

## Recommendation

Use the fixed weighted-recency method for Version 1. Keep Add optional and Hide limited to the exact product. Don't fill a short personal list with discovery products. General-popularity fallback is a separate no-history scenario; new-customer effectiveness hasn't been measured.

The product goal is less searching for familiar groceries. Test equivalent basket-building tasks with and without the feature, measuring time alongside completion, incorrect additions and abandonment. No numeric acceptance threshold or controlled estimate of time saved is available. Two exploratory sessions reported search-first/suggestions-second times of about22/4 seconds and20/5 seconds. Repeated products, fixed order and first-session assistance limit interpretation. R02 needed no help and had both correct target products in each basket, as confirmed by Justin. These pilot records aren't a representative user study; see the research record for missing details.

## Evidence

[Final evaluation](03_Checks/final_evaluation.json) · [Matched local runtime](03_Checks/prediction_runtime.json) · [Decisions](02_Decisions.md) · [Research and testing](../01_Project/04_Research_And_Testing.md) · [Full case study](../01_Project/05_Portfolio_Case_Study.md).

The final answers are exposed. No further tuning or re-selection against them is part of Version 1. No revenue, retention or conversion impact is claimed.


## Version 2 timing experiment — development only

This is a separate cohort and target point; don't compare these values directly with Version 1's final results above. The same60,000 development customers were scored with the unchanged weighted-recency rule and one prospectively fixed timing-bonus rule.

| Measure | Weighted recency | Timing bonus |
|---|---:|---:|
| Mean Precision@5 | 37.302% | 37.374% |
| Mean Recall@5 | 24.556% | 24.581% |
| Hit Rate@5 | 79.560% | 79.557% |

The recall change was+0.0249 percentage points, with an approximate paired95% interval of-0.0027 to+0.0524 under independent-customer assumptions. It fell short of the fixed+0.25-point gate and the interval spans zero. Precision increased slightly and hit rate decreased slightly; these don't establish shopper benefit.

Timing was available for840,010 of3,618,144 development customer-product candidates; sparse candidates kept the baseline score. Both methods had1,580 short lists. The challenger gave more matches to2,028 customers, the same match count to56,137 and fewer to1,835. Ranked lists changed for20,731 customers; changed ranking doesn't imply better outcomes. The long-history subgroup's observed gain is exploratory, not a reason to choose a subgroup-specific winner afterward.

**Decision:** stop this fixed attempt, retain weighted recency and leave the15,000-person audit unscored. No prototype change. One timing formula's weak result doesn't rule out timing generally. [Fixed protocol](03_Checks/v2_timing_protocol.json), [preparation checks](03_Checks/v2_timing_preparation.json), [development result](03_Checks/v2_timing_development.json).

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
