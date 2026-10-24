# Data and methods

## Start with a basket

One customer can place several orders. Each order can contain several products. That's why the data comes in linked tables rather than one row per person.

If one order contains milk, bread and eggs, it's **one order with three product lines**. The data doesn't tell me how many cartons of milk were bought.

## The six source tables

| File | What one row means | Main columns |
|---|---|---|
| orders.csv | One order | order_id, user_id, eval_set, order_number, order_dow, order_hour_of_day, days_since_prior_order |
| order_products__prior.csv | One product in an earlier order | order_id, product_id, add_to_cart_order, reordered |
| order_products__train.csv | One product in a labelled final order | Same product-line columns |
| products.csv | One product | product_id, product_name, aisle_id, department_id |
| aisles.csv | One aisle label | aisle_id, aisle |
| departments.csv | One department label | department_id, department |

IDs are anonymous labels. An order ID identifies an order; a user ID groups the provided order history. Neither identifies a real person's name.

## Columns worth knowing

**order_number** tells me where the order sits in that user's sequence. Order 3 means their third provided order, not 3 products.

**reordered** is 1 when that user has bought the product before, and 0 otherwise. It refers to any earlier order, not necessarily the immediately previous one.

**add_to_cart_order** is the position of the product within the purchased basket. A value of 2 means it was the second product added. It isn't the number of cart actions and doesn't show products that were abandoned.

**days_since_prior_order** is the recorded gap since the previous order. It's blank for the first order. The value is capped at 30, so a value of 30 can mean 30 days or more. I'll keep that distinction when describing shopping frequency.

**order_dow** is a day-of-week code from 0 to 6. I'll keep those codes rather than assume which number means Monday or Sunday. **order_hour_of_day** runs from 0 to 23. Neither column gives an actual calendar date or a verified time zone.

## Prior, train and test

| Label | How I'll use it |
|---|---|
| prior | Earlier orders with known product contents. These form the purchase history. |
| train | A user's final order with known contents. I'll hold it back for a later check of the recommendations. |
| test | A user's final order whose contents aren't provided. I can't score a recommendation against it. |

An unknown test basket isn't an empty basket. Its product counts stay blank, not zero. Users have either a train or test final order in this release.

## Prepared files

| File | What's inside |
|---|---|
| instacart.duckdb | Original prepared database, retained; its engine is currently blocked by Windows on this computer |
| instacart_ml.sqlite | Current SQLite source cache and checked training/validation features; contains earlier orders, not final basket contents |
| products.csv | Product names joined to aisle and department labels |
| order_summary.parquet | One row per order, including known basket size and repeat-product count |
| product_history_metrics.csv | One row per product, with counts from prior orders only |
| department_history_metrics.csv | One row per department, with prior-order counts |
| evaluation_plan.csv | One labelled user, with the earlier validation order and final target order identified |
| learning_orders.csv | One selected user's order sequence for teaching |
| learning_order_items.csv | Products in that user's first three orders, with readable names |
| order_summary_sample.csv | A small preview of order_summary |

Parquet is a compact table format. DuckDB can read it directly, so there's no need to open millions of rows in Excel. The learning examples are selected for explanation and aren't a representative sample.

## Counting and evaluation rules

## Name the counting unit first

Orders, product lines and users answer different questions. I'll name the unit beside every measure and avoid treating a product-line count as a count of items by quantity.

## Descriptive measures

| Measure | Calculation | What it tells me |
|---|---|---|
| Basket size | Product lines in one known order | Number of different product entries, not units purchased |
| Repeat-line share | Lines with reordered = 1 / all product lines | Share of purchased product lines that repeat an earlier purchase |
| Product buyers | Distinct user IDs buying the product | Tracked users with that product in the chosen history |
| Product order count | Distinct orders containing the product | How often the product appears in recorded baskets |

Repeat-line share isn't the percentage of customers who return. It also isn't the chance that someone buys the product in their next order. Those need different denominators and observation rules.

The prepared product and department summaries use **prior orders only**. I'll calculate combined shares from summed counts, not by averaging product percentages. A zero denominator gives a blank rate.

## How the later recommendation check will work

The working plan is to offer **five products per user** and compare the lists with labelled later baskets. For each user:

- **Precision at 5:** how many of the five suggested products appear in the actual basket, divided by 5. An unfilled slot doesn't earn a hit.
- **Recall at 5:** correctly suggested products divided by all distinct products in the actual basket.
- **Hit rate at 5:** whether at least one suggestion appears in the basket. Across users, it's users with a hit divided by evaluated users.

I'll average user-level scores so customers with large baskets don't silently dominate the result. Both methods must use the same users and target baskets. These metrics describe overlap with later recorded purchases, not extra sales caused by recommendations.

## Keep later answers out of earlier decisions

For each labelled user, the last prior order is set aside for trying ideas. Only orders before it can supply validation features, popularity lists or candidate products. The final train-labelled basket stays separate until the method is fixed.

After choosing the method, all prior orders can supply history for the final check. The final train basket still can't be used as an input. Test baskets have unknown contents, so they're excluded from scoring rather than treated as missed purchases.

The ready-made product summaries include every prior order. They're useful for describing history but aren't safe validation inputs because they include validation targets. For the final popularity baseline, rebuild counts from the fixed evaluation cohort and allowed earlier-history cutoffs rather than blindly using the full-cohort summaries.

## Compare fairly

I'll choose minimum sample sizes before highlighting products, look at differences in available history, and keep any later method changes separate from the final check. I can also report performance on repeat products as a separate measure, with its own denominator.

The data doesn't have prices, quantities, profit or recommendation exposure. I won't turn an offline score into a claim about revenue lift or customer satisfaction. A real app test would need its own success metric and checks for unwanted effects.

## Data source

The dataset was released by Instacart in 2017. The working CSVs were retrieved on 20 October 2026 from an archived copy on Zenodo because the original S3 download returned an access error.

- [Original release article](https://tech.instacart.com/3-million-instacart-orders-open-sourced-d40d29ead6f2)
- [Original data dictionary](https://gist.github.com/jeremystan/c3b39d947d9b88b3ccff3147dbcf6c6b)
- [Original usage terms](https://gist.github.com/jeremystan/582eba13d6ee27ed465c43dc78934700)
- [Archive used for the working files](https://zenodo.org/records/2654444)

The archive's published checksums are used to check the downloaded files. Source URLs, hashes and retrieval details are in `05_Results/03_Checks/source_manifest.json`.

Instacart describes the release as a selected, biased sample. Conclusions will stay specific to these records. This is local, non-commercial learning work. I'll keep raw files and detailed prepared data out of a public repository and review the original terms before sharing results or any artifact that could expose row-level data.

## Visual style

The guide keeps the readable layout from the earlier project, using colours from the [Instacart brand guide](https://heyitsinstacart.com/color/):

| Colour | Hex | Use here |
|---|---|---|
| Kale | #003D29 | Headings, links and buttons |
| Cashew | #FAF1E5 | Sidebar and selected reading areas |
| Honeydew | #C5FF96 | Selected navigation and small highlights |
| Carrot | #FF7009 | A small decorative accent |
| Cashew 80 | #32302E | Body text |
| Cashew 60 | #716C67 | Supporting text |
| Cashew 30 | #E1D9CE | Borders |
| Cashew 050 | #FDF8F2 | Light surfaces |

Carrot and Lime are accent colours in the guide, so they won't become body text or large reading backgrounds. Buttons use a rounded shape. The page uses a system-font fallback rather than assuming access to Instacart's custom typeface.

The page is an independent portfolio project. Its design doesn't imply Instacart created, reviewed or endorsed the analysis.

## Preparation record

The source tables have been loaded and checked. These are preparation results, not conclusions about customers.

## What's in the files?

| Source table | Rows |
|---|---|
| orders | 3,421,083 |
| products | 49,688 |
| aisles | 134 |
| departments | 21 |
| order_products__prior | 32,434,489 |
| order_products__train | 1,384,617 |

There are **206,209 tracked users**. The order table includes 3,214,874 earlier orders, 131,209 labelled final orders and 75,000 final orders whose contents aren't provided.

## What was checked?

All six downloaded files match the checksums published by the archive. The preparation also checks unique table keys, order-product pairs, links between tables, split labels, valid codes, cart positions and consecutive order numbers. The structural checks passed. The detailed results are in `preparation_report.json`.

No source rows were removed or filled in. Unknown test contents stay blank. Missing category labels remain visible rather than being guessed.

## What needs care?

The first order's gap is expected to be blank. The value 30 means 30 days or more. Day-of-week codes stay 0–6, and no actual calendar dates or time zone are assumed.

Instacart says the release isn't representative of its entire business. The data doesn't show prices, quantities, abandoned carts or recommendation exposure. Results will describe this sample and any offline comparison, not proven business impact.

## Ready for later evaluation

There are 131,209 users with labelled final baskets. `evaluation_plan.csv` identifies an earlier basket for validation and a later target for the final check. Any validation inputs must stop before the earlier target; the full prior-history summaries include that target and aren't valid early-cutoff features.

These preparation checks describe the input data. Three simple methods and two ML challengers have since been validation-tested. Weighted recency is selected for version one; final evaluation is still ahead.


## Fixed final-evaluation plan — 22 October 2026

### The simple version

The first-version choice is already made: weighted recency. We will now predict one later basket per customer with the method fixed, then open the answers and check the predictions. We won't use the final results to secretly keep improving this version.

1. Keep the same 131,209 customers identified in `evaluation_plan.csv`.
2. Use each customer's allowed earlier orders to prepare new final-prediction clues.
3. Generate and save every method's predictions before opening final product answers.
4. Check those predictions against the labelled final baskets.
5. Report the result, including any weakness, without selecting a new winner from the final scores.

For customer 1, our existing metadata gives validation order 10 and final order 11. Final inputs can use orders 1–10. Order 10 was once the hidden validation basket; it is now legitimate earlier history for predicting order 11. The answer in order 11 still can't become a clue.

### Fixed cohort, history and candidates

Use all 131,209 rows of the existing evaluation plan, one final target per customer. Target ID is `final_target_order_id`; the maximum allowed earlier order number is `final_history_max_order_number`. Verify every target belongs to the same customer, is labelled train and occurs immediately after its allowed history. Unknown official test contents aren't scored, treated as empty or used as negative labels.

Build final features only from that customer's prior orders at or before the cutoff. Use all eligible history through that cutoff, including the former validation basket. No target products, final basket size or final reordered flags may enter a feature, candidate rule, popularity count or tie-break. The five ML input columns and definitions remain unchanged. Personal candidates are distinct products bought in eligible earlier orders; each method can choose at most five, with no unfamiliar filler.

### Fixed methods and ML handling

| Method | Final-prediction rule |
|---|---|
| General popularity | Recalculate product counts from eligible prior orders for the same evaluation cohort only. Rank by distinct-order share; ties by product ID ascending. Same five products for everyone. |
| Personal frequency | Recalculate counts/latest purchase at the final history cutoff; purchase count descending, latest purchase descending, then product ID ascending. |
| Weighted recency — selected default | Same fixed five-order half-life, sum and round to 12 decimals; score descending, latest purchase descending, then product ID ascending. |
| Logistic regression — comparator | Reuse the original saved scaler and learned weights. Transform the new final-history features with that scaler, predict, and rank by score descending, latest purchase descending, then product ID ascending. |
| Boosted trees — comparator | Reuse the original saved 100-tree model and settings. Score the same new final-history feature rows and use the same score/latest/product tie-break. |

**No ML refit.** We are checking the existing learned models on a later target, with refreshed history clues. Additional history changes the inputs, not the trained scaler/weights/trees. No new feature selection, half-life change, setting search or automatic early-stopping choice. General popularity can choose unfamiliar products; disclose that candidate difference from the four personal methods.

The offline check has no Hide choices or simulated exposure. Planned app controls aren't used to manufacture evaluation gains. The no-history fallback isn't measured as new-customer effectiveness here.

### Save predictions before scoring

The implementation must have a prediction stage that never opens the final product-answer table/file. It may read target IDs/order metadata from the saved plan, not target product contents. Save prediction lists and a run record containing method settings, feature order, source/model/code fingerprints and target/cohort identifiers. Hashing source bytes is an integrity check, not use of answer values.

Before unlocking scoring, check all customers are represented, each personal suggestion belongs to eligible earlier history, ranks/products are unique and list lengths equal min(5, candidates). Check no feature order number exceeds its cutoff. Independently reconstruct features/ranks for 100 fixed customers, where practical. Check frozen ML predictions match saved model arithmetic/reload and that their learned state hasn't changed.

Only after those checks and saved predictions, read `order_products__train.csv` for the plan's target IDs. Verify unique order-product pairs, complete target coverage and nonempty known baskets. Don't let answer-reading recalculate or replace predictions. The original source preparation already performed file/table integrity checks; 'held back' here means not used to tune/select/score methods, not a claim that no parser has ever read source bytes.

### Metrics and reports fixed before answers

Primary: mean per-customer Recall@5, matches / distinct actual basket products. Supporting: mean Precision@5 (matches / five, even on short lists), Hit Rate@5 and mean match count. Include all matching customers rather than filtering after seeing performance.

The primary relative comparison is selected weighted recency versus personal frequency. Also report popularity and both frozen ML comparators on matching final targets. Show paired mean differences and approximate 95% intervals using the customer-level difference mean plus/minus 1.96 times its sample standard deviation divided by the square root of the number of customers. These assume independent customer identifiers; they aren't guarantees about all shoppers or causal effects.

Reuse existing groups, without choosing flattering new cutoffs: eligible history 1–5, 6–15, 16+ orders; actual final basket products 1–5, 6–10, 11–20, 21+. Final basket size is diagnostic only. Report group counts and reconcile weighted group means with overall metrics. Review more/same/fewer matches, short lists, distinct-product coverage and each method's own top-ten concentration. Name the denominator beside each percentage. Group summaries remain exploratory.

Report this final check separately from validation. No final score is available yet. Local benchmark timings remain a separate warm prepared-input test; don't convert total final-scoring time into shopper wait time.

### What happens after the result

The +0.5 percentage-point working target was introduced for the tree experiment after earlier validation work; don't relabel it a pre-registered final-score threshold or live product-success rule. There is no invented absolute recall level that proves shopper benefit.

If technical checks fail, stop rather than publish a passing result. If the selected method's final predictive evidence is weak, report that weakness and reassess the project honestly; don't quietly tune or promote a comparator using these same final answers. A future iteration needs a newly separated holdout or new data. Technical bug fixes after scoring require disclosure of what was seen, what changed and whether the check is still a fresh evaluation.

This is a per-customer order-sequence test, not a calendar-time deployment simulation: actual dates aren't provided. The sample has representativeness limits, repeated known customers and no browsing/exposure/price/quantity data. Even a strong final prediction result can't establish time saved, sales lift or shopper satisfaction.

**Status:** procedure documented; prediction/scoring code not run for final targets. The next implementation step is the prediction-only stage and its checks.

