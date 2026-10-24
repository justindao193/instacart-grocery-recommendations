# Learning notes

## Version 3 walkthrough: from an idea to the shopping page

**Status: the recommendation comparison and first prototype are built. Visual review and discovery user testing are still open.** This chapter records the implementation; it doesn't mean I've already understood or independently practised every step. We can work through it together without building another model.

### 1. Why we added this version

Version 1 answers: “What might this shopper want to buy again?” It only recommends familiar products. Version 2 tested whether usual purchase gaps could improve that ranking; the first timing rule added too little value, so we stopped it.

Version 3 asks a different question: “What unfamiliar products might fit this shopper's past purchases?” We kept this in a separate **You might also like** section. New means absent from the history we have, not something the person has never bought anywhere.

### 2. Which data went in

We reused the existing Instacart order data. The development group contained 60,000 shoppers, 876,349 earlier orders and 8,838,134 product lines. A shopper can have many orders, and each order contains many products; that's why the record count is much larger than the shopper count.

Another 15,000 shoppers were reserved for the final discovery check. For each shopper, we used earlier orders as clues and the last known prior basket as the answer. Their official final test baskets still have unknown contents.

Development answers had already been inspected during Version 2. We disclosed that reuse instead of calling this a brand-new untouched experiment. The reserved discovery check was run later under a separate written plan. It is now used too.

### 3. Our starting comparison: popular unfamiliar products

A baseline is a simple method that gives another method something to beat.

We counted how many eligible earlier orders contained each product and divided by all eligible earlier orders. Then, for each shopper, we removed every product already in their history and chose the top three remaining products.

**Made-up example:** the general list starts with bananas, milk, eggs and apples. If this shopper already bought bananas and eggs, those products are removed before suggestions are selected. The final list isn't necessarily identical for everyone, because their exclusions differ.

### 4. How we found related products

We built connections between products using shared buyers. Each shopper counts once for each product in this calculation, even if they bought it repeatedly. This differs from the popularity baseline, which counts orders.

**Made-up example:** 100 shoppers bought pasta, 100 bought sauce, and 40 bought both. That overlap provides a possible connection. It doesn't prove they ate them together or that every pasta buyer wants sauce.

We adjusted the overlap for each product's popularity:

`connection strength = shared buyers / square root(buyers of product A × buyers of product B)`

For the made-up numbers above: `40 / square root(100 × 100) = 0.4`. That is a similarity score, **not a 40% chance of buying**. This calculation is called cosine similarity on buyer lists. The broader approach is item-to-item collaborative filtering: recommend products using patterns across people's purchases.

We fixed these choices before scoring this discovery attempt:

| Choice | What it means | Why it was included |
|---|---|---|
| At least 50 buyers per product | Very rare products don't form similarity links | Avoid relying on extremely sparse evidence |
| At least 5 shared buyers | One shared shopper isn't enough for a link | Require some repeated evidence |
| Up to 40 neighbours per product | Keep its strongest related products | Keep the computation and saved model manageable |
| Up to 10 personal seed products | Start from the shopper's strongest recency-scored familiar products | Connect suggestions to their own history |

These were fixed implementation choices, not proven best settings. We didn't search many settings or establish that these limits are optimal.

### 5. How one shopper gets three suggestions

`Earlier purchases → strongest familiar products → related candidates → remove familiar products → rank → three suggestions`

Each seed product contributes points to its related products. Its contribution is its weighted-recency score multiplied by the connection strength. If several seed products point to the same unfamiliar item, their contributions add up.

**Made-up example:** pasta contributes 0.6 points to a sauce and tomatoes contribute 0.3. The sauce gets 0.9 points. That is a ranking score, not a 90% purchase probability.

We exclude the shopper's whole recorded product history, not just the ten seeds. Scores are rounded to 12 decimal places; product ID breaks exact ties. If related products don't fill three places, unfamiliar popularity fills the remaining places. This is called a fallback: a backup rule when the main method can't supply enough suggestions.

This version didn't use logistic regression or boosted trees. It calculated and saved product relationships, then reused them to rank candidates.

### 6. What the code actually does

| File in 03_Code | Inputs → actions → outputs |
|---|---|
| `03_Model_Comparison/prepare_discovery_baseline.py` | Reads development history from SQLite → counts orders per product → saves the general popularity ranking |
| `03_Model_Comparison/evaluate_discovery.py` | Reads earlier development histories → builds product connections → ranks unfamiliar products → saves both methods' lists → checks development answers and saves results |
| `04_Final_Evaluation/evaluate_discovery_audit.py` | Reuses the fixed development relationships and popularity → personalises to reserved shoppers → saves suggestions in its prepare stage → checks answers in its separate score stage |
| `05_Prototype/export_discovery_shoppers.py` | Reads fixed relationships and existing A/B example histories → exports three unfamiliar products and names into the HTML; doesn't read basket answers |
| `05_Prototype/buy_again_prototype.html` | Reads the small saved lists → renders cards → handles Add/remove, shopper switching and the basket |

SQLite is the local database that stores tables. SQL selects records from it. Python handles preparation, ranking and checks. A sparse matrix stores the shopper/product links that exist rather than millions of empty cells. JSON stores small structured records such as results and settings. HTML provides the page, CSS styles it, and JavaScript handles clicks and displayed state.

The scripts contain named functions, which are reusable groups of instructions. In the development script, `select` filters familiar products, ranks candidates and fills gaps; `digest` calculates a file fingerprint; `save` writes a report; `main` runs the workflow. In the audit script, `prepare` saves predictions and `score` checks them afterward. These aren't separate AI agents.

### 7. How we kept the checks fair

We wrote down the methods and metrics before scoring, and saved suggestions before opening that stage's answers. A file fingerprint, also called a hash, helps check that a saved file hasn't changed. It doesn't prove the whole method is correct on its own.

For the reserved check we reused the development-built product relationships and popularity ranking without refitting. Reserved shoppers' own earlier histories personalised their lists; they didn't change the shared product connections. We checked matching customer groups, personal-history exclusions, sampled rankings and raw CSV basket matches.

We kept discovery separate from familiar-product evaluation. Comparing its three unfamiliar suggestions directly with Version 1's five familiar suggestions would answer a different question.

### 8. What success meant

| Measure | Simple question | Denominator |
|---|---|---|
| Hit Rate@3 | Did any suggestion appear in the next basket? | All shoppers in that stage |
| Precision@3 | How many of our three suggestions matched? | Three slots per shopper, then average shoppers |
| Novel-product Recall@3 | How much of the shopper's new-product set did we find? | Novel target products per shopper, averaged only where that set isn't empty |

A shopper who bought nothing new still counts in hit rate and precision. We don't divide recall by zero; instead we report its separate eligible group explicitly.

The exploratory project gate was at least +0.5 percentage points in hit rate, a positive lower end of the approximate paired uncertainty interval, and no precision loss. We retained the same thresholds for the audit. They weren't an industry standard or a customer-benefit target.

### 9. What happened

| Stage | Shoppers | Popularity hit rate | Related-product hit rate |
|---|---:|---:|---:|
| Development | 60,000 | 6.56% | 7.78% |
| Reserved check | 15,000 | 6.63% | 7.73% |

The reserved-check improvement was **1.10 percentage points**. That is a net **165 more shoppers with at least one match**. Compared with popularity, 569 gained a hit, 404 lost a hit and 14,027 had the same hit/no-hit outcome. The approximate interval for the gain was +0.69 to +1.51 points, assuming independent shoppers with the shared fitted relationships treated as fixed.

Reserved precision was 2.35% versus 2.74%. Novel-product recall was 1.79% versus 2.20%, measured on the 12,253 shoppers whose next basket contained novel products. The other 2,747 still counted in overall hit rate and precision.

The improvement cleared the fixed gate. But most shoppers still had no matching suggestion. No match doesn't mean dislike: they may have no need for it in that particular order. We can't claim recommendations caused purchases, because nobody saw these historical recommendations when placing those orders.

### 10. How the website uses it

The page doesn't process millions of records or retrain when someone opens it. Python exported a tiny set of saved suggestions. JavaScript displays that set for the selected example shopper.

- A and B use their existing historical examples, separate from the reserved evaluation cohort.
- Buy it again still shows familiar items; You might also like shows unfamiliar ones.
- Both sections share the existing basket. Add/remove changes the displayed basket, not the recommendation model.
- C is simulated with no history. It keeps the popular-products section without a duplicate discovery row.
- Discovery currently has no Hide control; the existing familiar-product Hide works as before.
- Three new products have neutral image placeholders. Their names come from the source catalogue.
- Original Version 1 study links suppress discovery and keep their earlier catalogue, so we don't silently change the previous test conditions.

The code checks ran in Node with a simplified document stand-in. That checks JavaScript logic but doesn't show how a real browser looks or how a person experiences it. There hasn't been a new discovery user test or full visual/accessibility review.

### 11. What is done and what remains

| Done | Still to do |
|---|---|
| Baseline and related-product method | Walk through these ideas together where needed |
| Development comparison and reserved check | Review the actual discovery page visually |
| Saved reports, checks and learning records | Test whether people understand and find the new section useful |
| First discovery UI with basket interactions | Replace image placeholders if desired |

The reserved answers are now exposed. We mustn't keep changing the method until it looks good on those answers and then call that a fresh final test. A later model revision needs a new evaluation plan and suitable unused evidence.

My product decision was to explore discovery separately rather than change Buy again's purpose. Codex implemented and checked this extension with my approval and recorded the evidence. Writing this chapter doesn't certify my understanding; the next lesson can start with shared buyers and one small made-up example.

### Lesson recap — 24 October 2026: connections and code

We walked through the complete discovery flow with small examples and one real Trail Mix suggestion. Shared buyers means people who bought both products anywhere in their earlier orders, not necessarily together. Each person counts once per product for product connections. Similarity adjusts the overlap for the popularity of both products; it isn't a purchase probability.

Personal weighted recency × connection strength gives one contribution. Contributions add across familiar seed products. Soda contributed about1.51 points to Shopper A's Trail Mix score; Beef Jerky about1.38 and Pistachios about1.01, with other contributions bringing the total to5.44. These are actual saved-history calculations, distinct from the made-up arithmetic examples used during the lesson.

We covered the 50-buyer/five-shared-buyer evidence rules, up to40 neighbours, up to10 personal seeds, familiar-product exclusion, ranking three and popularity fill. Corrections practised: a familiar item is excluded even with a higher discovery score; two related suggestions need one fallback, not three; each customer counts at most once in hit rate. No match doesn't prove dislike and prototype Add doesn't prove willingness to pay.

The process diagram linked the two inputs: other shoppers' histories establish product connections; this shopper's history supplies personal weights. We then covered a binary shopper/product table, `purchases.T @ purchases` for shared counts, nested loops for contributions, `+=` for accumulating points and `[:3]` for taking three. These snippets were simplified teaching examples. The real code includes support filtering, rounding, tie-breaking and fallback.

Justin acknowledged these explanations; independent coding ability or mastery hasn't been assessed. He explicitly said reserved-test basics were already covered, so don't repeat that lesson unasked. The code walkthrough is complete as a lesson; the next useful activity is reviewing the actual discovery row and observing whether people understand it. No new UI review or discovery study happened in this lesson.

### 12. Where the evidence lives

Paths below are relative to the project folder. The existing files are the record; we don't need duplicate lesson documents.

- `05_Results/03_Checks/discovery_protocol.json` and `discovery_development.json`: fixed development method and results.
- `05_Results/03_Checks/discovery_audit_protocol.json`, `discovery_audit_preparation.json` and `discovery_audit.json`: reserved plan, predictions-before-answers checks and results.
- `05_Results/03_Checks/discovery_verification.json`: additional ranking/exclusion checks.
- `05_Results/03_Checks/discovery_demo_export.json` and `discovery_prototype_checks.json`: example export and UI logic checks.
- `04_Learning/03_Notebooks/02_Recommendation_Methods.ipynb`: saved-result previews; use those cells without rerunning old builders.
- `01_Project/04_Research_And_Testing.md`: proposed discovery walkthrough; no new sessions claimed.
- `04_Learning/02_Learning_Log.md`: dated work milestones.


## Latest milestone: discovery passed the reserved check

We tried the same two methods on 15,000 reserved shoppers. We kept the product relationships and settings unchanged, saved the suggestions first, and only then checked the baskets.

- Popular unfamiliar products matched something for **6.63%** of shoppers.
- Related unfamiliar products matched something for **7.73%**.
- That's **165 more shoppers with a match**, overall. Some gained a match and some lost one.

The improvement held up and cleared our fixed project criteria. It supports trying the idea in the prototype; it doesn't prove people will enjoy the suggestions or buy more. Most still had no match in their next basket.

**What I learned:** development is where we explore an idea; a reserved check tests the fixed choice on another group. Once we've checked those answers, they aren't untouched anymore. Changing the method to suit those answers would require a different test to make a fair final claim.

Hit rate and precision included all 15,000 shoppers. Novel-product recall included the 12,253 whose next basket contained something absent from their recorded history. No discovery section has been added to the shopping page yet. Earlier sections describe earlier stages.

## Project wrap-up — 23 October 2026

The analysis, working prototype and case study are complete for this learning project. Weighted recency remains the selected method. Portfolio presentation and publishing are separate next steps.

### What I learned from start to finish

| Part | What I learned |
|---|---|
| Understand the data | One customer can have many orders. A product line isn't a quantity, and missing information isn't automatically zero. |
| Make a fair comparison | Use earlier orders as clues and a later basket as the answer. Compare methods on the same customers and baskets. |
| Start simple | Popularity gives everyone the same list. Personal frequency uses their own habits. Weighted recency gives recent purchases more points. |
| Try machine learning | Logistic regression learns weights for clues; boosted trees combine small decision rules. Extra complexity needs a useful benefit. |
| Measure results | Precision asks how many of the five suggestions matched. Recall asks how much of the actual basket we found. Hit rate asks whether there was at least one match. |
| Make a product decision | Trees scored slightly better, but I chose weighted recency for an easier-to-inspect first version. It wasn't the highest-accuracy method. |
| Build and test | Saved recommendations can power a small HTML prototype. Button checks, prediction checks and tests with people answer different questions. |
| Read user feedback carefully | Two people were faster on their second task, but they repeated the products. Practice and help mean we can't claim the feature caused the time saving. |
| Know when to stop | The first timing experiment added too little improvement to adopt. Keeping a simpler method is a valid outcome. |

### Version 2 in simple terms

We kept the original recency score and added a small bonus when a product's usual gap between purchases lined up with the next order. Products without enough history kept their original score. This was a fixed rule, not another trained model.

On the same 60,000 development customers, recall went from **24.556% to 24.581%**: about **0.025 percentage points**. The project criterion was at least 0.25 points, and the uncertainty range included no improvement. This attempt didn't earn a place in the prototype. It doesn't prove that timing can never help.

We stopped without scoring the 15,000 reserved customers. We didn't move the target after seeing the result or change the shopping page.

### What stays open

A more controlled user study, full accessibility and app-speed checks, independent setup reproduction and public deployment are future work. Unchecked learning exercises are optional practice, not proof that the completed analysis is missing. I haven't demonstrated independent mastery of every topic simply because the implementation is finished.

## What I'm building

Help returning grocery shoppers find products they might need again. I'll compare a general popular-products list with suggestions based on each customer's past purchases.

The data comes from Instacart's public 2017 grocery-order release. It records historical baskets, not people interacting with our recommendation tool. The project uses documented archive copies; source details are in the project guide.

## The data

| Term | Meaning |
|---|---|
| Customer ID | One customer can have many orders |
| Order ID | One grocery basket |
| Product line | One product in an order, not the quantity bought |
| Reordered | Bought by this customer in an earlier provided order |
| Days since the last order | 12 means 12 days; 30 means 30 or more days |

One basket with five different products is **one order and five product lines**. The first recorded order has a blank previous-order gap. Zero would incorrectly mean a zero-day gap.

## What buying history tells us

| Clue | Question |
|---|---|
| Frequency | How often do they buy it? |
| Recency | How recently did they buy it? |
| Timing | Might they need it again soon? |

Past behaviour is a clue, not a guarantee. Repeated oat-milk purchases support suggesting oat milk, but don't prove someone is vegan. The data doesn't directly record dietary restrictions, prices, quantities, browsing or reasons for buying. `add_to_cart_order` is position within a purchased basket, not an abandoned-cart event.

## Precision, recall and hit rate

| Measure | Simple meaning | Calculation |
|---|---|---|
| Precision@5 | How much of our list did they buy? | Matches / 5 suggestions |
| Recall@5 | How much of their basket did we predict? | Matches / actual basket products |
| Hit rate@5 | How many customers had any match? | Customers with at least one match / evaluated customers |

For example, two matches among five suggestions and four actual products means **40% precision** and **50% recall**. Precision and recall are calculated per customer, then averaged. Empty suggestion slots still count against precision's denominator of five.

Customers never saw these suggestions. Better overlap means better prediction, not proof that suggestions caused a purchase or saved time. That needs a future customer test.

## How a fair test works

Use earlier baskets to make suggestions and keep a later basket hidden until scoring. We can try ideas on validation baskets; the final evaluation stays separate until the method is fixed.

The personal methods focus on rebuying familiar groceries. We suggest up to five products; the app and final evaluation are still ahead.

## Understand and check the real data

We started by following one customer's baskets, checking the tables and deciding what to do with missing categories.

## One real customer

Customer 1's first three recorded baskets, with shortened product names:

| Order | Products |
|---|---|
| 1 | Soda, almond milk, beef jerky, popcorn, paper towels |
| 2 | Soda, pistachios, beef jerky, bananas, popcorn, cereal |
| 3 | Soda, beef jerky, pistachios, string cheese, almond butter |

Pistachios and popcorn both appear twice. Pistachios have the stronger recency signal because they appear in orders 2 and 3; popcorn appears in 1 and 2. Soda and beef jerky appear in all three. This example describes one customer, not all shoppers.

Source: `02_Data/02_Prepared/learning_order_items.csv`.

## What passed

The saved structural checks found no missing or duplicate main IDs, invalid product/order links or duplicate order-product pairs. The checks support reliable joins; they don't establish that the sample represents every Instacart customer.

## Missing categories

**1,258 products** have a department labelled `missing`. We agreed to retain them and use **Unknown** in reporting. The source labels remain unchanged; the display transformation hasn't been implemented yet.

| Measure | Calculation | Result |
|---|---|---|
| Catalogue share | 1,258 / 49,688 products | 2.53% |
| Prior purchase-line share | 69,145 / 32,434,489 lines | 0.21% |

They account for less purchasing activity than their catalogue share suggests. Guessing departments could distort the comparison.

[Practice the check](03_Notebooks/01_Data_And_SQL.ipynb).

## Set up the validation baskets

The dataset's order labels tell us what history and hidden baskets are available.

## Prior, train and test

| Group | Orders | Share of all orders | Our use |
|---|---|---|---|
| Prior | 3,214,874 | 93.97% | Earlier purchase history |
| Train | 131,209 | 3.84% | Hold back the final labelled basket |
| Test | 75,000 | 2.19% | Products unknown; cannot score accuracy |

The denominator is **3,421,083 orders**. Each customer has several prior orders and one final order labelled either train or test.

## Our history cutoffs

For eligible train customers, validation uses the last prior basket, with inputs built only from earlier orders. Once we fix the method, we'll use all prior history to predict the official train basket. We haven't run that final evaluation.

## Build the popularity baseline

**Rule:** suggest the five products appearing in the highest percentage of eligible history orders. Everyone receives the same list.

Popularity = orders containing the product / all eligible history orders.

We used **1,916,168 eligible past orders**, ending before each customer's validation basket.

| Product | Share of eligible orders |
|---|---|
| Banana | 14.72% |
| Bag of Organic Bananas | 11.71% |
| Organic Strawberries | 8.28% |
| Organic Baby Spinach | 7.53% |
| Organic Hass Avocado | 6.73% |

Banana appears in 282,094 eligible orders. These shares describe past baskets, not individual future purchase probabilities. Products can share a basket, so percentages don't add to 100%. The two banana products have different IDs.

Customer 1 had **zero matches** in their nine-product validation basket. Overall hit rate was **35.81%** (46,985 / 131,209 customers).

[Build the list](03_Notebooks/02_Recommendation_Methods.ipynb) | [Check the scores](03_Notebooks/02_Recommendation_Methods.ipynb)

## Build personal favourites

**Rule:** count each customer's earlier purchases. Rank products by purchase-order count, then latest purchase order, then product ID. Recency only breaks a tie here.

Customer 1 received Soda, Original Beef Jerky, Pistachios, Organic String Cheese and Zero Calorie Cola. **All five matched their nine-product basket.** That's one example; the overall comparison is in Results so far.

**3,521 customers had fewer than five past products.** We left those lists shorter instead of adding filler. Precision still divides by five.

This method only suggests familiar products. General popularity can suggest unfamiliar products, so the candidate strategies differ even though the scoring baskets are the same.

[Read the method and results](03_Notebooks/02_Recommendation_Methods.ipynb).

## Investigate what we missed

This diagnosis uses the **personal-frequency method**, before weighted recency.

| Miss type | Product lines | Share of missed lines |
|---|---|---|
| Familiar product not suggested | 566,649 | 50.21% |
| Absent from eligible personal history | 561,873 | 49.79% |

Denominator: **1,128,522 missed product lines**, pooled across validation baskets. These aren't customer percentages or average recall. New-to-history doesn't mean never bought in life.

Not every familiar miss is a ranking mistake: five suggestions can't match six familiar products in one basket. The report separates this capacity limit from what a hypothetical perfect ranking could recover. That ceiling uses hidden answers for diagnosis, not as a real prediction method.

[Understand the missed products](03_Notebooks/03_Model_Diagnostics.ipynb).

## Give recent purchases more weight

**Rule:** add points for each purchase, giving older purchases less weight.

| Purchase age | Points |
|---|---|
| Latest eligible order | 1 |
| Five order positions older | 0.5 |
| Ten order positions older | 0.25 |

Age means **order positions, not days**. Sum the points for each product, then select up to five. Ties use latest purchase order, then product ID. We chose this five-order rule before scoring; we haven't proved it's the best setting.

Recall rose from **23.44% to 24.54%: +1.10 percentage points**. The method still only suggests familiar products. Customer 1's suggestions were unchanged.

[Read the weighting rule and scores](03_Notebooks/02_Recommendation_Methods.ipynb).

## Check different customer groups

History means earlier orders available for prediction; the hidden basket doesn't count.

| Past orders | Customers | Frequency recall | Weighted-recency recall | Change |
|---|---|---|---|---|
| 1–5 | 46,929 | 23.00% | 23.02% | +0.02 points |
| 6–15 | 45,262 | 24.39% | 25.08% | +0.69 points |
| 16+ | 39,018 | 22.87% | 25.75% | +2.88 points |

The largest average gain is in long history. This doesn't prove a cause or show everyone improved: **17,716 customers had more matches, 104,799 the same and 8,694 fewer**. Short-history hit rate changes slightly downward even though recall rises slightly.

Groups also differ in basket size and habits. The approximate uncertainty intervals in the reports don't establish population representativeness or causal value.

[Frequency by history](03_Notebooks/03_Model_Diagnostics.ipynb) | [Recency by history](03_Notebooks/03_Model_Diagnostics.ipynb)

## How the five methods differ

All five methods choose up to five products, but they choose them differently.

| Method | How it chooses | Simple way to explain it |
|---|---|---|
| Popularity | Ranks products by their share of eligible earlier orders across customers. Everyone gets the same list. | These products are popular overall. |
| Personal frequency | Ranks a customer's familiar products by purchase count. Latest purchase breaks ties, then product ID. | I buy this product often. |
| Weighted recency | Gives each earlier purchase points, with older purchases worth less. | I've bought this product more in my recent orders. |
| Logistic regression | Learns how to combine the five history clues from examples with known next-basket answers. | Considering the clues together, this product gets a higher score. |
| Boosted trees | Learns a sequence of small decision trees that add adjustments to the earlier predictions. | The right score can depend on combinations of clues. |

The first three follow rules we chose. Logistic regression learns its weights from training examples. Weighted recency uses our chosen five-order half-life: a purchase five order positions older gets half the points. Popularity can suggest unfamiliar products; the three personal methods only choose from each customer's eligible earlier purchases.

A more complicated method doesn't automatically give better predictions. Our first logistic model is almost tied with weighted recency on validation recall, with slightly lower precision and hit rate. That's evidence about this attempt, not a conclusion that machine learning can never help.

## Validation results

| Method | Precision | Recall | Customers with a match |
|---|---|---|---|
| Popular products | 9.31% | 4.71% | 35.81% |
| Personal favourites | 35.13% | 23.44% | 78.07% |
| Recent purchases weighted | 36.91% | 24.54% | 79.16% |
| First logistic regression | 36.88% | 24.55% | 79.13% |
| First boosted trees | 37.15% | 24.71% | 79.33% |

Same **131,209 customers and validation baskets** for all five. These are prediction scores, not measured improvements in shopping or sales.

For customers without history, general popular products are a planned fallback. This dataset doesn't directly evaluate brand-new customer outcomes.

## Product versions

**Version 1: Buy again.** Help returning shoppers find familiar groceries. Up to five suggestions, factual reasons, a demo basket, exact-product Hide and restore, and a performance view. Hidden products are saved per example customer in the same browser. Add is optional; ignoring a product isn't proof of dislike. The ML challenger, final evaluation and Streamlit demo remain part of the planned work. Controls aren't built yet.

**Version 2: Better coverage — proposed.** Test useful new-to-customer suggestions, products bought together or purchase timing. Choose the improvement based on evidence; don't expand every feature at once.

**Version 3: Learn from use — proposed.** Collect permitted exposure and interaction feedback and test adaptation. Measure time and successful completion with new observations. The existing order data can't establish those benefits.

The first case study can finish with Version 1. Later versions are a roadmap, not extra promises. Don't reuse an already-inspected final test as a fresh test for later iterations.

## Logistic regression: the first ML challenger

Logistic regression learns how to combine clues to estimate whether a familiar product will appear in the next basket. Despite its name, we're using it for a yes-or-no outcome. During training, earlier-history clues are paired with a next-basket label: 1 for bought, 0 for not bought. Zero doesn't mean dislike.

Each row represents one customer, one familiar product and one prediction point. All inputs must come from before the target basket. Training uses known answers to learn weights; evaluation hides its answers until scoring. We rank eligible products by score and select up to five, rather than requiring scores above 50%.

Our fixed rules use weights we chose. Logistic regression learns weights from examples. Its scores are estimated probabilities, not guarantees; we haven't checked their calibration. A learned weight isn't proof that a clue causes a purchase.

### Inputs in the first model

| Input | What it describes |
|---|---|
| Purchase count | How many earlier orders contain the product |
| Purchase share | Product purchase count / customer's eligible earlier orders |
| Orders since last purchase | How many order positions have passed since they bought it |
| Weighted-recency score | More points for recent purchases, using our existing five-order half-life |
| History length | Number of eligible earlier orders available |

Eight purchases in ten orders is an 80% share; eight in a hundred is 8%. Eighteen purchases in twenty orders provide more evidence of a repeated habit than one in one. However, simply including share and history length doesn't guarantee logistic regression learns that reliability relationship: transformations or interactions may be needed and must be evaluated.

These inputs are now built in the initial SQLite feature table; final feature selection is still open. Purchase count, share and history length overlap, so we'll check redundancy and use appropriate scaling and regularisation when building the model. Usual purchase gaps and elapsed time are later candidates, not part of the initial proposal. They need enough repeats, careful missing-value handling and acknowledgement that 30-day gaps mean 30 or more days.

Inputs are different from evaluation measures. We'll compare methods using mean Recall@5, Precision@5 and Hit Rate@5 on matching customers and baskets, plus runtime and complexity. A simpler method can remain the demo choice. The first logistic model is now fitted and validated below. No calibration test or app response-time benchmark has been run.

## Scaling and regularisation

**Scaling** changes the numerical ruler, not the underlying purchase history. Each input has its own training-data average and spread. A scaled value of zero means at that input's training average; it doesn't mean no orders. Negative values are below average, positive values above it. For the made-up values 5, 10 and 15 orders, the scaled values are about -1.22, 0 and +1.22.

Learn the rulers from training rows only, then reuse them unchanged for validation and later predictions. The original values remain unchanged. This helps the regularised model work with inputs expressed on different numerical scales. The implementation uses StandardScaler, which subtracts the training average and divides by the training standard deviation (a measure of spread).

**Regularisation** restrains excessively large learned weights. Too little restraint can fit quirks in the learning examples; too much can stop the model using useful patterns. Fitting quirks that don't hold up later is called overfitting. Good training performance alone isn't the goal: we compare predictions on later validation baskets. Regularisation doesn't guarantee a good model or calibrated probabilities.

The first attempt uses standard L2 regularisation with C=1.0, fixed before seeing its validation result. We haven't searched for a best setting. In this parameter convention, a smaller C means stronger restraint. Scaling and the model are joined in a pipeline: an ordered set of steps that keeps the same learned adjustments attached to the model.

## Preparing the ML inputs with SQLite

Windows Smart App Control blocks DuckDB's native file on this computer. We kept the security settings enabled and switched this preparation step to Python's built-in SQLite engine. SQL still describes the calculations; SQLite runs them. Earlier DuckDB scripts and their saved results remain available, but their old notebook cells haven't all been converted.

The checked local file is `02_Data/02_Prepared/instacart_ml.sqlite`, table `ml_features`. Both stages cover the same 131,209 customers:

| Stage | Customer-product rows | Purpose |
|---|---:|---|
| Training | 7,324,671 | Earlier examples for learning the model's weights |
| Validation | 7,912,788 | Later examples for comparing methods |

These are product candidates, not millions of separate customers. Each customer contributes multiple familiar products. For validation order v, training predicts order v-1 using inputs through v-2; validation predicts order v using inputs through v-1. No final basket contents are imported.

The five input columns are purchase count, purchase share, orders since last purchase, weighted recency and history length. The `bought_next` column is the answer; customer/product IDs and cutoff fields are for linking/checking records, not model inputs.

Checks passed for duplicate candidates, history cutoffs, value bounds and customer coverage. Independent calculations from the original CSVs matched both stages for ten customers. Recreating personal frequency and weighted recency in SQLite matched their saved aggregate validation scores for all three metrics. This confirms those comparisons; it isn't a new model result or a shopping-benefit test.

[Inspect the feature preview](03_Notebooks/02_Recommendation_Methods.ipynb), in the last section. Run that preview cell independently: earlier DuckDB cells still have the Windows block. The preview reads checked data and doesn't rebuild or fit anything.

## First logistic-regression result

We fitted one model using all 7,324,671 training rows and the five prepared inputs. StandardScaler learned its averages and spreads from training only. Logistic regression used L2 C=1.0, fixed before looking at this attempt's validation result. We didn't search settings, balance classes or sample away negative examples.

| Validation measure | Logistic regression | Weighted recency |
|---|---:|---:|
| Mean Precision@5 | 36.884% | 36.907% |
| Mean Recall@5 | 24.546% | 24.543% |
| Hit Rate@5 | 79.133% | 79.161% |

Same 131,209 customers and complete validation baskets. The recall difference is about +0.0027 percentage points; precision and hit rate are slightly lower. This attempt hasn't established a clear improvement over weighted recency. The approximate paired recall interval spans zero (-0.0166 to +0.0219 percentage points) under independent-customer assumptions. This isn't proof that all ML approaches are equivalent or that either saves shopping time.

The scaler stayed unchanged during validation. Checks independently confirmed top-five ranking/overlap for 100 customers, portable weight-based predictions and exact cohort/target alignment. Both methods have 3,521 short lists and precision still divides by five. Recall uses the full actual basket, including products absent from personal history.

The weights and training ruler are saved locally in `02_Data/03_Model_Outputs/logistic_model.json`; validation recommendations and per-customer scores are in `logistic_validation.sqlite` in the same folder. Aggregated evidence is in `05_Results/03_Checks/logistic_validation.json`. The saved-results section at the end of the Recommendation methods notebook reads this comparison without retraining.

The fit took about 4.5 seconds, with about 32.6 seconds for this whole validation scoring/ranking pass. These aren't app response-time measurements or a fair runtime comparison against other methods. No final basket was loaded or scored in this experiment. The later sections record the tree experiment and subsequent version-one choice. Calibration, the demo and live benefit testing remain ahead.

## What the model code does

The simple flow is: **read earlier shopping records → practise with known answers → finish training → predict later baskets → keep five → check and save**.

We choose which clues to provide; the model learns their weights. During training it uses known answers to adjust those weights. After training, prediction reuses the saved weights without changing them. Validation answers are used afterward to measure matches, not supplied to the prediction call. Our first fit stopped after 17 adjustment rounds; it isn't continuously learning now.

The script is [train_logistic_validation.py](../03_Code/03_Model_Comparison/train_logistic_validation.py). It now shares its evaluation checks with the tree experiment; the walkthrough below follows its logistic route. [train_boosted_validation.py](../03_Code/03_Model_Comparison/train_boosted_validation.py) calls that runner with the tree model selected. This explanation doesn't rerun either model.

**1. Read the checked learning material.** SQLite stores the prepared tables. Python reads the training rows, taking only the five agreed input columns and the next-basket answer.

```python
X = training[FEATURES].to_numpy(dtype=np.float64)
y = training['bought_next'].to_numpy(dtype=np.int8)
```

`X` holds the clues. `y` holds the answers: 1 for bought next, 0 otherwise. `FEATURES` is the list of five input column names. `to_numpy` turns table columns into numerical arrays, which are organised collections of numbers the model can process. The `dtype` choices specify how those numbers are stored. Customer IDs and answer columns aren't used as clues.

**2. Connect scaling and learning.** A pipeline is a sequence of steps applied in order.

```python
model = make_pipeline(StandardScaler(), LogisticRegression(**SETTINGS))
model.fit(X, y)
```

`StandardScaler` learns the training rulers. `LogisticRegression` learns how strongly to combine the clues, with regularisation restraining its weights. `SETTINGS` contains our fixed choices for this attempt; `**SETTINGS` passes them into the model. `fit` means learn from the supplied examples. The pipeline first scales the inputs, then trains the model on them.

**3. Score the later validation examples.** The trained model reuses its training rulers and weights; it doesn't learn again from validation answers.

```python
probabilities = model.predict_proba(values)[:, 1]
```

`values` contains the validation clues. `predict_proba` returns estimated chances for no and yes. `[:, 1]` selects the yes score for each row. A score is an estimate, not a promise that someone will buy the product.

**4. Choose and check five suggestions.** The rest of the code keeps the five highest-scoring familiar products per customer, or fewer if fewer candidates exist. Scores tied exactly are ordered by latest purchase, then product ID. It compares the selected products with the later basket and calculates precision, recall and hit rate.

**5. Verify and save.** The script checks that the training rulers didn't change, independently checks ranking and matches for 100 customers, and saves the learned weights, rulers, recommendations and validation results. It never loads or scores the official final baskets. The later selection section records the version-one choice; real shopping benefit is still unmeasured.

## Decision trees and boosting

A decision tree learns a sequence of questions about the purchase-history clues. A made-up example might first ask whether a product was bought in the last two orders, then whether it appeared in at least half the earlier orders. Different answers lead to different scores. The training algorithm learns the actual questions and cutoffs; this example isn't our fitted tree.

Boosting builds a team of small trees in sequence. Each later tree learns adjustments that help reduce the remaining training errors. Their adjustments combine into one final product score. We still select up to five familiar products per customer. The training answers guide learning; validation answers aren't passed into the fit.

Justin correctly followed the example: a product bought recently but in only two of ten orders reached the middle-score branch.

For the next fixed experiment, we're using scikit-learn's histogram gradient boosting classifier with the same five inputs and identical training/validation baskets. Histogram means the implementation groups input values into ranges to make training efficient. Tree splits use the original input values, so this attempt doesn't need StandardScaler. This doesn't change the earlier scaling lesson for regularised logistic regression.

The first tree attempt is fixed at 100 rounds, learning rate 0.1, at most 15 leaves and depth 4 per tree, minimum 100 training examples per leaf and L2 regularisation 1.0. Leaves are the endpoints where a tree supplies its adjustment. Learning rate controls how strongly each new tree contributes. No class balancing or negative sampling. Early stopping is disabled so there is no automatic random-row validation split; all 100 rounds use training examples only. These are starting choices, not proven optimal settings.

The proposed working recall-gain target is +0.5 percentage points versus weighted recency, with precision, hit rate, groups and runtime reviewed too. This is an experiment target stated before this result, not a researched business threshold or final deployment rule. No final evaluation baskets are used.

## First boosted-tree result

We ran one fixed attempt, changing the model while keeping the five inputs, 7,324,671 training rows, familiar-product candidates and validation baskets the same. No setting search or new features. It finished 100 training rounds, then the frozen model scored 7,912,788 validation candidates for 131,209 customers.

| Validation measure | Weighted recency | Logistic regression | Boosted trees |
|---|---:|---:|---:|
| Mean Precision@5 | 36.907% | 36.884% | 37.146% |
| Mean Recall@5 | 24.543% | 24.546% | 24.707% |
| Hit Rate@5 | 79.161% | 79.133% | 79.329% |

Tree recall improved by about **0.164 percentage points** over weighted recency. The approximate paired interval is +0.136 to +0.192 points under independent-customer assumptions. The proposed working +0.5-point target wasn't met. This is a modest measured validation improvement, not proof of shopping benefit or a final method decision.

| Earlier orders available | Weighted-recency recall | Tree recall |
|---|---:|---:|
| 1–5 | 23.023% | 23.052% |
| 6–15 | 25.076% | 25.300% |
| 16+ | 25.753% | 26.011% |

These are group averages, not proof every customer improved. Product coverage and a fair app-response-time comparison remain open. This run's fit took about 27.9 seconds and its validation scoring/ranking pass about 35.7 seconds. They are local batch timings, not shopper wait times or a controlled cross-model benchmark.

Checks passed for the same customers/target baskets, unchanged fitted model during prediction, 100 independently sorted top-five lists and overlaps, saved-model prediction reload and the existing weighted-recency reference. Saved logistic customer-level scores were aligned by customer, target and full basket size. All three personal model variants still have 3,521 short lists. Final basket contents weren't loaded or scored.

The tree entry script reuses our existing validation code to keep scoring consistent. Its model is saved locally as `02_Data/03_Model_Outputs/boosted_trees_model.joblib`; detailed suggestions/scores are in `boosted_trees_validation.sqlite` in that folder. Load only model files created and trusted by us. Aggregate evidence is in `05_Results/03_Checks/boosted_trees_validation.json`. The final section of the Recommendation methods notebook reads the saved comparison without retraining.

The later selection section records the decision after reviewing these trade-offs. No additional setting search was run.

## Accuracy and complexity: deciding what earns its place

Justin raised an important point: we should consider model complexity as well as accuracy. A small improvement doesn't automatically justify a more complicated system.

| Consideration | Weighted recency | Logistic regression | Fixed boosted trees |
|---|---|---|---|
| Calculation | One chosen purchase-weighting rule | Learned weights applied to scaled inputs | 100 learned small trees |
| Explanation | Trace each purchase's contribution | Inspect the combined clue weights; correlated clues need care | Harder to explain the full combined prediction |
| Maintenance | Rule and history calculations | Features, scaler, training and saved weights | Features, training settings and saved trees |
| Validation Recall@5 | 24.543% | 24.546% | 24.707% |
| Warm calculation on prepared inputs | About 0.005 ms median | About 0.204 ms median | About 0.541 ms median |
| Warm retrieval of a saved list | About 0.041 ms median | About 0.041 ms median | About 0.041 ms median |

Both depend on reliable input data. Neither is maintenance-free. The matched local speed check below found both calculations fast; it doesn't measure what a shopper would wait in a deployed app. The earlier batch runtimes aren't a response-time comparison.

The tree recall gain is +0.164 percentage points overall. By history group the gains are about +0.03 points for 1–5 earlier orders, +0.22 for 6–15 and +0.26 for 16+. Justin correctly identified the 16+ group as having the biggest average gain. Even that group average is below the proposed +0.5-point experiment target; group averages don't show how every individual did.

I selected weighted recency as the version-one default on 22 October 2026, keeping both ML experiments in the portfolio comparison. Testing a more complex approach and explaining its limited gain is useful evidence of judgment. No final evaluation has been run.

## Individual customers: more, the same or fewer matches

An average improvement can include customers who improved and customers who got worse. We paired every customer's tree and weighted-recency results on the same validation basket and full basket size.

| Tree outcome versus weighted recency | Customers | Share of all validation customers |
|---|---:|---:|
| More matching suggestions | 6,794 | 5.18% |
| Same number of matches | 119,054 | 90.74% |
| Fewer matching suggestions | 5,361 | 4.09% |

Denominator: **131,209 customers**, counted once each. Rounded percentages may not sum to exactly 100%. Same number of matches doesn't necessarily mean the same products were suggested. These are prediction outcomes, not measured shopping experiences.

| Earlier orders | More matches | Same matches | Fewer matches |
|---|---:|---:|---:|
| 1–5 | 310 | 46,383 | 236 |
| 6–15 | 3,247 | 39,500 | 2,515 |
| 16+ | 3,237 | 33,171 | 2,610 |

Checks confirmed the same customer IDs, target orders, basket sizes and history lengths. Group counts reconcile to the full cohort, and individual outcomes reproduce the saved aggregate precision, recall and hit rate for both methods. The report is `05_Results/03_Checks/tree_customer_tradeoffs.json`.

This comparison reads saved validation evidence and the existing features; it doesn't fit another model. The SQLite route is in `03_Code/03_Model_Comparison/compare_recency_groups.py` with `--trees`. The Model diagnostics notebook reads the saved report. The matched local speed check is now recorded below. Full app response time remains open; weighted recency is now selected for version one.

## Speed check: calculation versus loading saved suggestions

The first timing comparison included weighted recency and trees. Justin correctly pointed out that logistic regression should be included too. We corrected the code and reran **all three methods together**, rather than mixing numbers from different runs. This table supersedes the earlier two-method timing table.

We measured three separate jobs: fetching prepared product clues from SQLite and formatting them as numbers; scaling where needed, scoring and ranking; and fetching a suggestion list calculated and saved beforehand. The original logistic scaler and weights were restored without retraining. Logistic's timed calculation includes its normal scikit-learn scaling and prediction steps. Restored predictions were independently checked against the saved weight equation and saved validation lists.

The same 90 customers were used: 30 per history group, selected before timing by a fixed hash rule. Each operation had three warm-ups and 20 measured repeats per customer. Method order was randomised with the same seed, with two threads and identical candidates/tie-breaks. All three cached-list methods used the same small temporary disk SQLite database, which was removed afterward.

Median means the middle measurement. The 95th percentile means 95% of these calls took no longer than that time. A millisecond (ms) is one thousandth of a second.

| Measured job | Median | 95th percentile |
|---|---:|---:|
| Shared feature fetch and formatting | 0.139 ms | 0.259 ms |
| Weighted-recency ranking | 0.005 ms | 0.011 ms |
| Logistic scaling, scoring and ranking | 0.204 ms | 0.288 ms |
| Boosted-tree scoring and ranking | 0.541 ms | 0.756 ms |
| Fetch saved weighted recency list | 0.041 ms | 0.054 ms |
| Fetch saved logistic regression list | 0.041 ms | 0.055 ms |
| Fetch saved boosted trees list | 0.041 ms | 0.056 ms |

All three prepared-input calculations were fast locally. Logistic regression sat between the simple ranking rule and trees in this run, while fetching saved lists was nearly identical. This doesn't justify a claim that any method caused a noticeable shopper delay. The accuracy gain and explanation/maintenance trade-offs remain more relevant.

This warm, sequential local benchmark excludes building features from raw history, model load, cold starts, network and app rendering. The small cache isn't production-size, groups aren't weighted to the full population, and the repeated calls aren't independent customers. Don't add stage medians and call that measured app latency. The result applies to these implementations and this computer; small timing differences between runs are expected.

Checks passed for stable predictions, identical candidates/ties, matching saved tree AND logistic lists, matching logistic weight-equation predictions, and cached lists matching calculation. No refit or final basket reading/scoring. Evidence: `05_Results/03_Checks/prediction_runtime.json`; reproduce through `03_Code/03_Model_Comparison/compare_recency_groups.py --benchmark`. The Model diagnostics notebook reads the current saved report without rerunning timings.

Weighted recency is now selected for version one. The full iteration and decision are recorded below. Full app response time comes after an app exists.

## Product coverage: how widely suggestions are spread

Coverage asks how many different products appear in our suggestions across all customers. Concentration asks how much of the suggestion space is taken by the most commonly suggested products. For Buy again, broader coverage isn't automatically better: each shopper still needs relevant familiar products.

We compared the same 131,209 validation customers across weighted recency, logistic regression and boosted trees. The eligible pool contained **49,371 distinct products** appearing in their earlier personal candidate lists; it isn't the full 49,688-product catalogue or the products from their hidden next baskets.

| Method | Different products suggested | Share of eligible product pool | Top 10 products' share of suggestions |
|---|---:|---:|---:|
| Weighted recency | 29,138 | 59.02% | 11.31% |
| Logistic regression | 29,128 | 59.00% | 11.32% |
| Boosted trees | 29,271 | 59.29% | 11.18% |

Coverage denominator: 49,371 eligible distinct products. Concentration denominator: **648,697 filled suggestion slots** for each method; a slot is one product suggested to one customer. The top-ten set is each method's own ten most frequently suggested products, with ten fixed before inspecting results. This describes concentration across customers, not variety inside one person's list.

Trees cover slightly more products and are slightly less concentrated, but the differences are small. Banana, Bag of Organic Bananas and Organic Baby Spinach are the leading three products in all three methods. These counts don't establish product availability, exposures, customer demand or sales impact.

All three give **3,521 customers fewer than five suggestions**: 2.68% of 131,209 customers. They each fill 98.88% of the five-slots-per-customer maximum (648,697 / 656,045). The same short lists arise from fewer than five familiar candidates; changing the ranking model can't create more familiar products for these customers. We didn't silently add unfamiliar filler.

The comparison reused saved ML lists and rebuilt only the existing weighted-recency ranking. Checks confirmed identical customer IDs/target orders, unique ranks/products, every suggestion in that customer's eligible earlier history, expected list lengths and consistent totals. No models were fitted and no final basket contents were read or scored.

Evidence is in `05_Results/03_Checks/product_coverage_validation.json`. Reproduce it with `03_Code/03_Model_Comparison/compare_recency_groups.py --coverage`; the Model diagnostics notebook reads the saved summary.

The selection below combines accuracy, individual gains/losses, coverage, speed and maintenance. Weighted recency is now selected for version one despite the modest tree gains. The basket-size review is complete below; final-evaluation procedure and prototype acceptance criteria remain open. No final scoring or app build has occurred.

## Basket size: interpreting scores fairly

These groups describe the number of different products in the actual validation basket, not how many earlier orders a customer has. We fixed the groups at 1–5, 6–10, 11–20 and 21+ products before inspecting the results. Actual basket size is only used afterward to check performance; it isn't supplied to a prediction.

| Actual basket products | Customers | Weighted-recency recall | Logistic recall | Tree recall |
|---|---:|---:|---:|---:|
| 1-5 products | 40,010 | 38.98% | 39.02% | 39.23% |
| 6-10 products | 39,628 | 22.31% | 22.31% | 22.49% |
| 11-20 products | 37,937 | 16.32% | 16.30% | 16.43% |
| 21+ products | 13,634 | 11.54% | 11.53% | 11.59% |

Recall is matches divided by the actual basket's product count, calculated per customer and then averaged. With only five suggestions, bigger baskets have a lower possible recall. Five correct suggestions cover 100% of a five-product basket, but only 25% of a twenty-product basket. That structural limit doesn't prove a ranking problem. It also ignores the extra restriction that our suggestions must be familiar products.

Trees improved mean recall over weighted recency by about +0.250, +0.175, +0.105 and +0.044 percentage points in the four groups. Those gains are small. They don't imply every metric improved: in the 21+ group, tree hit rate was 95.071%, slightly below weighted recency's 95.086%.

Bigger baskets also offer more opportunities for a suggestion to match. Weighted-recency precision rose from 21.93% in the smallest group to 60.79% in the largest, even while recall fell. Look at precision, recall and hit rate together rather than calling large-basket recommendations worse based on recall alone. These are observational groups, not evidence that basket size causes a model's performance.

The 40,010 / 39,628 / 37,937 / 13,634 customers sum to all 131,209 customers, counted once. Checked exact customer, target and complete basket-size alignment for all three methods. Group-weighted means reproduce all saved overall precision, recall and hit-rate results. No training or final basket reading/scoring.

Report: `05_Results/03_Checks/basket_size_validation.json`. Reproduce with `03_Code/03_Model_Comparison/compare_recency_groups.py --basket-size`; the Model diagnostics notebook reads the saved comparison. The selection below uses this diagnostic with the other evidence. Final evaluation rules still need to be fixed before opening final answers.

## My iteration: why I chose weighted recency

I started with a general popular-products list, then made the suggestions personal by counting past purchases. That improved prediction substantially. Next, I gave recent purchases more weight using a fixed five-order half-life. This improved recall again while keeping the rule easy to trace.

I then tried logistic regression to learn how to combine the clues. It performed almost the same as weighted recency. I tested boosted trees next to see whether a more flexible model could do better with the same inputs. Trees did improve accuracy and coverage slightly, but the recall gain was only about +0.164 percentage points, below the proposed +0.5-point working target.

Before choosing, I also reviewed customer gains/losses, history length, actual basket size, product coverage and speed. Most customers had the same number of matches. All three personal methods were fast locally, so I didn't use speed as an unsupported reason to reject trees.

**I chose weighted recency as the version-one default because its balance of accuracy, explanation and maintenance suited this first demo.** I accepted a small reduction in measured validation accuracy in exchange for a simpler method. I kept the ML experiments as evidence of the alternatives I tested, rather than calling the selected method the most accurate.

This was a comparison of five tested approaches, not all possible models. Final evaluation and the app are still ahead. Historical purchase predictions don't prove that shoppers save time or buy more.

[Read the full decision and selected rule](../05_Results/02_Decisions.md).

## The final check: use more history, keep the method fixed

Weighted recency is selected. Next we'll use the later final basket to check the fixed choice, alongside the same comparison methods.

Customer 1 gives a concrete example: validation predicted order 10 using orders 1–9. Final prediction can use orders 1–10 to predict order 11. The former validation basket is now earlier history. That's allowed; using products from order 11 as clues wouldn't be.

The learned ML models won't train again. We update their purchase-history inputs, but keep the original logistic scaler/weights and tree model. Weighted recency keeps its same five-order rule. Save every prediction list first, then open final answers to calculate the scores. Don't keep changing the model after seeing those answers.

Primary measure is mean per-customer Recall@5, with precision, hit rate, customer groups, coverage and short lists alongside it. The final result is a later check, not proof of shopper benefit or a new contest to select a winner. If the evidence is weak, report it honestly and use a fresh holdout for any new iteration.

[Read the fixed evaluation procedure](../01_Project/03_Data_And_Methods.md). It is now documented; final predictions and scoring haven't run.

## Final prediction lists saved before answers

The prediction-only stage is complete. All five fixed methods have saved lists for the same **131,209 customers**, using only their earlier history through the final cutoff. The original logistic scaler/weights and tree model were reused without training again. Weighted recency kept the selected five-order rule.

The refreshed feature table has 8,474,661 customer-product rows, built from 2,047,377 eligible earlier orders. Customer 1's final cutoff is order 10, so the lists predict order 11. No final target product answers were opened by this script and no accuracy scores were generated.

| Method | Customers | Saved suggestions | Customers with fewer than five |
|---|---:|---:|---:|
| Popularity | 131,209 | 656,045 | 0 |
| Personal frequency | 131,209 | 651,660 | 2,168 |
| Weighted recency | 131,209 | 651,660 | 2,168 |
| Logistic regression | 131,209 | 651,660 | 2,168 |
| Boosted trees | 131,209 | 651,660 | 2,168 |

The personal methods have fewer short lists than during validation because the final inputs contain one more earlier basket and therefore can contain more familiar candidates. That's a history change, not proof that the ranking model improved. Popularity can fill all five by suggesting products outside personal history; disclose that difference.

Checks passed for target metadata, complete earlier-order sequences, valid feature values, unique ranks/products, familiar-product eligibility, expected list lengths and unchanged ML state/files. Independently rebuilt feature values from original prior CSVs for 100 customers and sorted all five methods' lists independently. A small known-answer test confirmed the former validation history is included while a final target purchase is excluded. The first run's empty connection file was removed after inspection and SQLite URI handling corrected before the successful build; it contained no feature or prediction tables.

The frozen local artifact is `02_Data/03_Model_Outputs/final_predictions.sqlite`. It has target metadata, final-history features and recommendation lists, with no answer or accuracy table. The report `05_Results/03_Checks/final_prediction_preparation.json` records checks and source/model/code/plan hashes. A hash is a fingerprint of file contents; the later scoring stage can use it to check it is reading the saved artifact. Preparation refuses to overwrite an existing final artifact.

Next: read the final basket answers only for scoring these fixed lists. That is a separate step. Don't regenerate predictions, refit models or change the chosen method after seeing final scores. The existing Model diagnostics notebook has a read-only report preview, not a new preparation run.

## Final evaluation: the saved lists have now been scored

We verified the exact saved prediction file, sources, model files, generating code and frozen plan fingerprints before reading the final product answers. Then we compared the fixed lists with the same 131,209 customers' labelled final baskets. No predictions were regenerated and no ML model was retrained. The scoring code can't choose new products.

These are **final-check results**, separate from the earlier validation tables:

| Method | Mean Precision@5 | Mean Recall@5 | Hit Rate@5 |
|---|---:|---:|---:|
| General popularity | 9.48% | 4.69% | 36.24% |
| Personal frequency | 35.41% | 23.12% | 78.23% |
| Weighted recency — selected | 37.32% | 24.28% | 79.37% |
| Logistic regression | 37.30% | 24.28% | 79.38% |
| Boosted trees | 37.58% | 24.45% | 79.45% |

For weighted recency, 37.32% precision means about 1.87 matches among five suggestion slots on average. Recall of 24.28% means the list captured about that share of actual basket products, averaged per customer. Hit rate of 79.37% means that share of customers had at least one match. These measures answer different questions; none proves the suggestions caused a purchase.

### What the final check tells us

- Selected weighted recency beat personal frequency by about **+1.160 percentage points Recall@5** on these later baskets. Its approximate paired 95% interval is +1.112 to +1.208 points under independent-customer assumptions.
- Logistic regression was again nearly tied with weighted recency: about +0.0027 points recall, with an interval spanning zero.
- Trees were more accurate: **+0.176 percentage points recall** over weighted recency, with approximate interval +0.148 to +0.205 points. Acknowledge that measured gain; don't describe weighted recency as the most accurate.
- Weighted recency remains the preselected version-one default because the choice prioritised simpler explanation/maintenance for a modest accuracy trade-off. We didn't choose a new winner from the final results. The earlier +0.5-point tree experiment target isn't retroactively a pre-registered final business success rule.

Final and validation scores shouldn't be mixed or interpreted as a before/after product lift. They use different target baskets and different amounts of earlier history. The learned ML weights/scaler/trees stayed fixed.

### Checks, groups and limits

All 1,384,617 final product lines formed unique order-product pairs, covering all target baskets with no empty known basket. Per-customer matches and all three metrics were independently reconstructed from the raw final CSV for 100 customers per method. Fixed history/basket groups reconcile to overall scores. Full paired comparisons, more/equal/fewer matches and coverage are in the report. All four personal methods kept the same 2,168 short lists and 651,660 filled slots; popularity filled 656,045 slots and can suggest unfamiliar products.

Final-history groups have 38,076 / 51,519 / 41,614 customers for 1–5 / 6–15 / 16+ earlier orders. Actual final-basket groups have 39,359 / 39,002 / 38,409 / 14,439 customers for 1–5 / 6–10 / 11–20 / 21+ products. These groups use final histories/targets, so their counts differ from validation. Bigger baskets still have the five-slot recall limit.

The final eligible product pool is 49,468. Weighted recency suggested 28,721 different products, logistic 28,749 and trees 28,973. Their own top-ten concentration was about 11.74%, 11.74% and 11.59% of filled slots. These are descriptive coverage measures, not new-product discovery or customer-value evidence.

**This holdout has now been inspected.** We must not tune against it or call a later rerun a fresh unseen test. A future model change needs a newly separated evaluation plan or new data. Historical biased data, approximate intervals, known customers and absent browsing/exposure/price/quantity information limit claims. No live experiment, time saving, revenue lift or satisfaction improvement was measured.

The frozen prediction artifact remains unchanged. Detailed local scores/answers are in `02_Data/03_Model_Outputs/final_scores.sqlite`; do not publish those detailed rows. Aggregated results/checks are in `05_Results/03_Checks/final_evaluation.json`. The code is `03_Code/04_Final_Evaluation/score_final_predictions.py`, which refuses to overwrite an existing final scoring artifact. The Model diagnostics notebook reads the saved final report without rerunning evaluation.

Next: review the final result together, then plan the first Streamlit screen and implement the selected Buy again experience. The app isn't built yet, and the portfolio findings/recommendations should still be written together.

## Prototype: turning the method into a screen

A **prototype** is a clickable mock-up that shows how a feature would feel before it's properly built. Ours lets a reviewer pick an example shopper, see up to five Buy again cards, add some to a demo basket, hide one and restore it.

A **state** is one version of a screen in a particular situation. For example, Shopper B only has three familiar products, so the "short list" state shows three cards and says that's everything they've bought before. We designed normal, added, hidden, restored, short-list, empty, no-history, loading and error states.

**Mock data** means placeholder content used to show the layout. The product names are real catalogue names, but the "Bought in 9 of 12 earlier orders" counts are placeholders until we export real examples. The prototype labels this.

Requirements are in 01_Project/07_Prototype_Requirements.md. The prototype is 03_Code/05_Prototype/buy_again_prototype.html. It simulates the Hide/restore rules in the browser; it doesn't run the Python algorithm and hasn't been tested with people.

## Where we stopped

**Now:** final evaluation passed its checks. Weighted recency remains selected for version one; final recall is 24.28%, versus 23.12% frequency, 24.28% logistic and 24.45% trees. Review the separate final section, not the earlier validation table.

**Completed since this stage:** final evaluation, an HTML prototype, exploratory user sessions and the case study. No Streamlit rebuild is needed. The final holdout has been inspected and can't be reused for tuning.

Findings and product decisions are recorded in the project guide. The full checklist stays in Learning path.


## AI tools and skills

I'll learn these as we use them in the project. This is a short reference, not a list of things I need to master first.

| Thing | What it does | Example from this project | Status |
|---|---|---|---|
| AGENTS.md | Saves instructions for how the AI should work | Teach one idea at a time and correct mistakes kindly | Created |
| 01_Project/06_Project_Context.md | Saves a checkpoint that the AI can read later | Records where the data lesson stopped | Created |
| scikit-learn | Provides tested machine-learning tools in Python | Ran a small scaler/logistic-regression fit and prediction check; used for the first challenger | Used |
| SQLite through Python | Runs SQL locally without the blocked DuckDB module | Built and checked training/validation feature rows | Used |
| File-reading tool | Lets the agent inspect saved files | Read the current AGENTS.md before changing it | Used |
| File-editing tool (apply_patch) | Makes specific changes to text files | Added the AI learning rules without replacing the guide | Used |
| OpenAI Docs skill | Guides the agent to official documentation for OpenAI questions | Checked how project instructions and skills work | Used |
| Web browsing tool | Retrieves online information | Read the tutorial and official instruction-file documentation | Used |
| Claude device file tools | Let Claude read and write files in a folder on this computer after I approve access | Read the project docs and saved the prototype and requirements here | Used |
| Claude browser pane | Opens real web pages so Claude can look at layout and styles | Checked instacart.ca and the Instacart brand guide for colours, buttons and fonts | Used |
| Playwright | Opens a page in an invisible browser and clicks through it automatically | Checked that Hide, Undo, Restore, short-list and no-history states behave as designed | Used |
| Claude Projects | Keeps shared documents Claude can read in later chats | Added the handoff, working rules, brief, research, decisions and prototype requirements | Used |
| Figma connector | Would let Claude read or edit Figma files | Not connected yet; the prototype was made as HTML first | Planned |

## Things to remember
- A tool performs an action. A skill gives a reusable way to do a job and may include scripts or templates.
- An agent uses the model, instructions, context and tools to work through a task.
- Saving a preference in a file doesn't retrain the model. The agent needs to read the relevant file to use it.
- A tool being available doesn't mean it was used. Keep examples tied to actions that actually happened.

## Try it later
Open AGENTS.md and find the rule about teaching one idea at a time. That's a project instruction. The file-editing tool is what changed the file.

## Future entries
As we use something new, add a short explanation, a real project example and a small action I can try myself. Keep planned ideas separate from completed work.


## Connecting the prototype to real examples

The HTML prototype is now an interactive shopping example using saved recommendations. Python exports a small set of checked history summaries into the page, so the browser doesn't need to load millions of rows or retrain a model. A has 18 familiar products; B has only one. C is a simulated shopper with no history.

We keep every familiar candidate for A/B, not just five. Hide filters the candidate list first, then the next product can fill the space. Zero orders since the last purchase means the product was in the latest known order. Counts support the quiet Often bought and Last order tags.

These checks answer different questions: saved-basket evaluation checks prediction accuracy; button tests check behaviour; observing people checks whether the interface is understandable. None alone proves shopping time saved. The later prototype and pilot sections record the completed checks and their limits.


### Current prototype connection

Claude's approved design now displays two real historical examples using our saved weighted-recency recommendations. The design and the recommendation data are separate: we can update the small data export without rebuilding the interface or retraining a model. A/B are real examples; C is simulated. All candidates are available for Hide replacements. Photos remain illustrative, and products without one use a placeholder. The seven browse groups are simplified demo categories. The updated file is in the project folder; the Downloads reference still uses sample histories.


## Version 1: the portfolio story

The final decision is weighted recency. Its downside is slightly lower measured accuracy than the tested boosted trees, not a demonstrated inability to grow. I accepted that trade-off for a method that's easier to explain and maintain. Final mean recall was 24.276% for weighted recency and 24.452% for trees; the difference is 0.176 percentage points.

The case study and findings now explain the problem, data, iteration, fair testing, result and product choices. The prototype uses saved real examples; it doesn't retrain in the browser. Informal feedback isn't proof of time saved. Screenshots, a fresh browser review, full app timing and publishing remain separate work. I don't need another model to finish Version 1.


## Version 2: purchase timing — first attempt

The extra clue was a product's usual gap between shopping trips. We used the median gap (the middle gap after sorting) and how much those gaps varied. At least three earlier purchases were needed for two gaps. With too little history, the score stayed exactly as Version 1's weighted recency. For the next-basket prediction, the elapsed gap is measured to the next order, not just the last observed order.

One fixed rule gave a bounded bonus for a consistent pattern lining up with the next order. No model was trained and no settings search was run. The 75,000-person cohort differs from Version 1's evaluated customers but comes from the already loaded public dataset; it isn't newly collected or guaranteed entirely unseen data. We fixed 60,000 development customers and left 15,000 in reserve.

| Development measure | Weighted recency | Timing bonus |
|---|---:|---:|
| Mean Precision@5 | 37.302% | 37.374% |
| Mean Recall@5 | 24.556% | 24.581% |
| Hit Rate@5 | 79.560% | 79.557% |

Both methods use the same 60,000 customers, familiar candidates and full target baskets. Recall improved by only about0.025 percentage points, versus the prospectively fixed0.25-point project gate. The approximate paired 95% interval (-0.003 to +0.052 points) includes zero. A plausible idea doesn't necessarily add useful predictive information beyond recency.

We stopped this first attempt, kept the prototype unchanged and didn't score the reserve. This isn't proof timing can never help, or that all irregular buyers are predictable. Any explanation for the weak gain is a hypothesis until checked. A later attempt would need a new plan that acknowledges the development results we've already seen. Saved reports are under05_Results/03_Checks/v2_timing_*.json; the Recommendation methods notebook reads them without rerunning anything.

## Version 3: discovery — started, not evaluated

Buy again asks “which familiar products might they want again?” Discovery asks “which unfamiliar products might fit their past shopping?” Unfamiliar means not seen in the recorded history, not never bought anywhere.

Our starting comparison will be popular unfamiliar products versus unfamiliar products connected to their past purchases. We first prepared the general ranking using earlier orders only. We still need to filter out each shopper's familiar products and build the related-product method. No discovery result exists yet.

A shopper might buy nothing new next time. We must keep those shoppers in the overall hit-rate calculation rather than quietly testing only people who tried something new. Discovery matches are prediction evidence, not proof our suggestions caused exploration.

## Version 3: how related-product suggestions work

Imagine two products are bought by many of the same shoppers. That gives us a possible connection. We count each shopper once for each product, so repeated orders don't give that person extra votes in the connection. We also adjust for how popular both products already are, rather than treating every popular product as a strong match.

For one shopper, we take up to ten of their strongest familiar products and let those products contribute points to related items. More recent favourites contribute more. Anything already in their recorded history is removed. We take three suggestions, filling any gaps with unfamiliar popular products.

This is an item-to-item recommendation method: products are connected using shared buyers. It doesn't know what a person likes, their diet or whether the products should be used together. We aren't training logistic regression again.

The first comparison found at least one match for about **7.78 out of 100 shoppers**, versus **6.56 out of 100** for popularity. That clears our exploratory comparison criterion, but roughly 92 out of 100 still had no matching suggestion. Not buying a recommendation doesn't prove dislike.

Hit rate and precision included all 60,000 shoppers. Novel-product recall included only the 49,118 whose next basket had something absent from their earlier history; dividing by zero for the others wouldn't make sense. The other 10,882 still count in the overall hit rate. This is different from our earlier full-basket Recall@5.

We haven't tested the reserved customers or added discovery to the shopping page. The next step is interpreting this result before a separately planned audit. These development answers had already been used in V2, so this isn't an untouched final test.

## Connecting discovery to the page

The browser reads a small saved list for A/B; it doesn't train a model. The new section is separate from Buy again because it suggests unfamiliar products. Both sections share the basket, so adding or removing a product updates every visible copy. C has no personal history and keeps the popular-products fallback.

An offline comparison checks prediction matches; code checks test interaction logic; observing people tests whether the screen makes sense. The discovery UI is built and logic-checked, but hasn't yet been visually reviewed or tested with people. Three new products currently use neutral photo placeholders.

## Five-card UI and why A/B overlap — 24 October 2026

Justin noticed similar discovery lists and requested five cards. We expanded only the illustrative prototype export from three to five, preserving the ranking and previous first three. Original @3 scores still describe three suggestions; they don't measure five-card accuracy or usefulness. No model was retrained or rescored.

A/B now share three of their five suggestions: Trail Mix, Clementines and the granola bars. This isn't popularity filling empty spots: all five in each example came from the related-product scores.

A has 18 familiar candidate products across ten earlier orders. Its Trail Mix score5.4402 combines several seeds, led by Soda1.5149, Beef Jerky1.3777 and Pistachios1.0058. B has just one familiar product across five earlier orders: Red Plastic Cups. Its whole discovery ranking therefore comes from that one item's saved neighbours. More orders don't automatically mean more varied history.

We independently checked development shared buyers:177 bought Red Plastic Cups,734 bought Trail Mix, and51 bought both somewhere in their earlier histories. Connection strength is51/sqrt(177×734)=0.14149. B's personal recency weight converts that into0.5465 points for Trail Mix. Cups also share buyers with Soda, Clementines and granola bars. Different seed products can therefore lead to overlapping suggestions.

This is a pattern in this historical dataset, not proof A and B have similar tastes or that cups cause snack purchases. A party-shopping explanation is plausible but unverified. B's narrow history gives the method little personal evidence; it doesn't know B's diet, preferences or reasons. Two examples can't establish how similar recommendations are across the whole population. Broader coverage/personalisation checks would be a separate analysis, not a reason to force example lists to look different.

New Pub Mix uses illustrative snack photography; Apples reuses an existing apples photo. All cards have embedded images. Five-card data/exclusion checks and fifth-card Add/remove checks passed in a stub DOM. Real browser visual review and discovery user testing remain open.
