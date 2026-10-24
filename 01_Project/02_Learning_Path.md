# Learning path

## Project status

**Complete as a learning project and local prototype — 23 October 2026.** The checklist below retains the original learning goals. Checked items have supporting records; unchecked items remain optional practice or future research/release work. They aren't all requirements for closing this project.

- [x] Complete the five-method comparison and record the weighted-recency decision.
- [x] Build the local prototype and record both exploratory user sessions and their limits.
- [x] Test one Version 2 timing rule and stop when it fails the fixed development criteria.
- [x] Add the timing result, final decision and lessons to the case study and learning notes.
- [x] Keep untested work visible and separate portfolio/publishing from this completed scope.

## The route

| Stage | What I'll leave with |
|---|---|
| 1. Define the problem | A clear shopper problem and a small first version |
| 2. Understand the data | A simple explanation of the tables and their limits |
| 3. Check the preparation | Confidence in how the analysis tables were made |
| 4. Explore buying patterns | Observations supported by numbers |
| 5. Plan a fair test | Agreed metrics and hidden baskets |
| 6. Build simple methods | Popular and personal recommendations |
| 7. Try machine learning | A challenger to the simpler methods |
| 8. Make the decision | An honest comparison and a chosen method |
| 9. Build the demo | A working HTML prototype; comparisons in the guide |
| 10. Review product value | Prototype feedback and a proposed real-world test |
| 11. Document the work | A case study, local run instructions and clear remaining checks |

## 1. Define the problem

**Output: a short product brief.**

- [x] Choose rebuying familiar products as the first-version focus.
- [x] Distinguish better prediction from proof of customer benefit.
- [x] Describe the target shopper and the situation we're trying to improve.
- [x] Separate known evidence from assumptions about searching and shopping effort.
- [x] Define what the first version will include and leave out.
- [x] Agree on success measures and the biggest risks.
- [ ] Set numeric success targets and define the prototype-test procedure before final decisions.

## 2. Understand the orders

**Output: explain one customer's baskets in plain English.**

- [x] Explain the difference between a user, an order and a product line.
- [x] Explain what `reordered = 1` means.
- [x] Explain why 30 means 30 or more days.
- [x] Follow one user's first few baskets in the actual data.
- [x] Learn why `add_to_cart_order` isn't a record of abandoned carts.
- [x] Explain why the first gap between orders is blank.
- [x] Learn the difference between prior, train and test orders.
- [x] Identify what's missing: prices, quantities, browsing and recommendation exposure.

## 3. Check the data preparation

**Output: a data-check summary I can explain.**

- [ ] Review where the files came from, their usage terms and saved file checks.
- [x] Review table keys, joins and the risk of accidentally multiplying rows.
- [x] Review missing values, duplicates, links between tables and row counts.
- [x] Check which orders have known contents before calculating a rate.
- [ ] Trace a raw record into a prepared table using SQL or Python.
- [ ] Review the preparation script and verification results; understand how to rerun them.

## 4. Explore buying patterns

**Output: a few useful observations, with evidence and limits.**

- [x] Compare basket sizes and available history across validation customer groups.
- [ ] Explore the distribution of gaps between orders.
- [ ] Compare product and department counts and repeat-purchase shares.
- [x] Practise stating order, customer and product-line denominators in our worked examples.
- [ ] Choose a minimum sample size before highlighting products.
- [ ] Check whether frequent shoppers or a few popular products dominate the story.
- [ ] Write findings together, separating observations from possible explanations.

## 5. Plan a fair test

**Output: a written evaluation plan before final scoring.**

- [x] Explain why a later basket must stay hidden when making recommendations.
- [x] Understand precision and recall.
- [x] Review the exact training, validation and final-evaluation history cutoffs.
- [x] Set candidate products, eligible users and rules for short recommendation lists.
- [x] Cover Hit Rate at 5 and per-customer averaging in the scoring walkthrough.
- [x] Use Recall@5 as the working primary measure, with precision and hit rate alongside it.
- [ ] Agree on a worthwhile improvement threshold before choosing the final method.
- [x] Discuss coverage, speed and complexity trade-offs, including saved suggestions.
- [ ] Set measurable coverage and response-time requirements before final decisions.
- [x] Check that compared methods use the same customers and hidden baskets.

## 6. Build simple recommendations

**Output: working methods and saved validation scores.**

- [x] Define popularity as the percentage of eligible past orders containing each product.
- [x] Explain frequency, recency and purchase timing using examples.
- [x] Decide what new customers see when they have no purchase history.
- [x] Build the five-product popularity baseline using eligible history only.
- [x] Build a personal-frequency method from each customer's earlier purchases.
- [x] Use purchase recency to break frequency ties, with product ID as the final tie-break.
- [x] Try giving recent purchases more weight and define how ties are handled.
- [x] Check examples manually and handle customers with fewer than five candidates.
- [x] Compare personal frequency and the fixed weighted-recency refinement on validation baskets only.

## 7. Try a machine-learning challenger

**Output: one model that earns its place through a fair comparison.**

- [x] Explain the prediction target and which products the model can choose from.
- [x] Build input features from eligible earlier orders only.
- [x] Understand training examples, labels and the risk of leaking future information.
- [x] Train a suitable first model and rank five suggestions per customer.
- [x] Explain that we choose the clues and the model learns their weights.
- [x] Distinguish using answers during training from checking predictions afterward.
- [x] Explain training-only scaling and reusing the same ruler during validation.
- [x] Explain regularisation and the risk of fitting quirks in training examples.
- [x] Walk through the script: read, learn, predict, select five, check and save.
- [x] Compare the first fixed logistic model with weighted recency on matching validation baskets.
- [x] Explain decision-tree questions and how boosting combines small-tree adjustments.
- [x] Run one fixed boosted-tree challenger with the same inputs and validation rules.
- [x] Stop additional tuning for version one and select the tested weighted-recency rule; retain ML challengers as comparison evidence.
- [ ] Explain important signals and review mistakes; don't treat them as causal explanations.

A simpler method can win. A more complicated model isn't automatically a better product.

## 8. Compare results and choose

**Output: a decision supported by results and trade-offs.**

- [x] Document the fixed methods, final history cutoffs, frozen ML comparators and reporting procedure before final scoring.
- [x] Generate, independently check and freeze all five methods' final predictions before reading final product answers.
- [x] Score the saved lists after fingerprint checks, independently verify matches and report final results separately from validation.
- [x] Calculate the validation precision, recall and hit-rate comparison on matching users.
- [x] Calculate paired validation score differences and approximate uncertainty intervals.
- [x] Discuss the practical size of the accuracy gain alongside explanation and maintenance effort.
- [ ] Interpret the uncertainty before locking a final method.
- [x] Compare the simple methods across the agreed history-length groups.
- [x] Compare product coverage, top-ten concentration and short lists for weighted recency and both ML challengers.
- [x] Compare all three personal methods by actual basket size and explain the five-suggestion recall limit.
- [x] Compare individual customers with more, equal or fewer matching suggestions.
- [x] Compare method complexity, explainability and maintenance needs.
- [x] Compare all three personal methods on warm local scoring/ranking, including logistic scaling, with data loading and saved-list retrieval separate.
- [ ] Measure full app response time once the app exists.
- [x] Choose weighted recency for the version-one demo and record the iteration, alternatives and trade-offs before final results.

## 9. Build the demo

**Output: an interactive HTML prototype, with comparisons in the project guide.**

- [x] Build a simple A/B/C shopper flow with up to five saved suggestions.
- [x] Connect two real historical examples without exposing target-basket answers as inputs; label simulated C in the project documentation.
- [x] Document the method choice and comparison outside the shopper interface, as requested.
- [x] Implement Add/remove, exact-product Hide, Undo, Show again, short and empty lists and a no-history fallback.
- [x] Check these rules and the custom shopper selector through JavaScript logic checks.
- [x] Record Justin's successful narrow-window layout check for search, Add and Basket.
- [x] Record Justin's successful basic Tab/Enter keyboard check for search, Add and Basket.
- [ ] Review remaining responsive sizes, all keyboard controls and loading/error states; the basic checks aren't a full accessibility audit.
- [ ] Measure full app response time; prepared-input benchmarks aren't app latency.
- [ ] Review the hosted example data and usage requirements before public deployment.

The current prototype is HTML; no Streamlit rebuild or Power BI dashboard is required. Screenshots must come from the real page. The browser tool currently blocks local file URLs, so assistant-captured screenshots and full visual review remain restricted. The owner-supplied desktop screenshot is saved.

## 10. Review the product idea

**Output: feedback notes and a proposed live experiment.**

- [x] Record the initial informal trial report and its limits; no measured completion rate or timings.
- [x] Separate informal prototype feedback from evidence of value to grocery shoppers.
- [ ] Prioritise changes by user value, effort and evidence.
- [x] Prepare a small comparison pilot for find/add time, completion, wrong additions and help; distinguish it from a live experiment.
- [x] Record the first timed pilot transcript and its assistance/practice limitations.
- [ ] Complete the planned comparison with verified conditions, baskets and help records before assessing benefit.
- [x] Explain why we haven't proved revenue growth or time savings with historical orders.
- [x] Record limitations, open questions and the next product decision.

## 11. Finish the project and case study

**Output: a project someone else can understand, run and discuss.**

- [x] Review local instructions, file links, pinned dependencies, launcher targets and safe imports without rebuilding results.
- [ ] Independently reproduce the analysis setup and main outputs in a separate environment without overwriting frozen artifacts.
- [ ] Keep raw data, detailed prepared data and the virtual environment out of public Git history.
- [x] Add source attribution, usage notes and clear prototype instructions.
- [x] Write the case study: problem, choices, evidence, result, trade-offs and next steps.
- [x] Review the final narrative against saved scores, both pilot records, the actual screenshot and remaining release checks.
- [x] Write a short prototype walkthrough in README.
- [x] Save the supplied desktop screenshot with an added product and basket, and include it in the case study.
- [ ] Capture phone and Hide/Undo views if needed for the final presentation.
- [ ] Prepare portfolio and resume wording after the remaining project work, as requested.
- [ ] Practise explaining the project and answering questions about the choices.
- [ ] Review deployment requirements and publish when requested.

## 12. Version 2: purchase timing

**Output: an honest comparison of a timing-aware rule and the Version 1 baseline.**

- [x] Check metadata for a separate customer cohort and disclose prior dataset exposure.
- [ ] Understand typical purchase gaps, irregular repeats and unavailable timing clues.
- [x] Fix one timing-aware rule, sparse-history fallback and prospective improvement criteria; distinguish project choices from business-agreed targets.
- [x] Create and freeze a customer-disjoint 60,000/15,000 development/audit split and cutoff-safe plan.
- [x] Build and check timing inputs from earlier history, including raw-record samples and synthetic cutoff/fallback checks.
- [x] Compare the fixed timing challenger against weighted recency on 60,000 development baskets.
- [x] Stop the first attempt after its development gate failed; retain the result and leave the reserved audit unscored.
- [ ] For any later justified attempt, fix a new plan and save audit predictions before inspecting audit product answers.
- [ ] Run and report an audit only for a candidate that passes its fixed development gate; no audit result exists for this attempt.
- [ ] Update the prototype only if a later candidate earns its place; no change justified by the first attempt.

## Throughout the project

- Keep the task board and decision log useful; update them when the work changes.
- Learn SQL, Python, AI tools and skills through the tasks where they're needed.
- Save useful explanations in Learning notes and the AI tools log.
- Record what I understand and what I still need to practise. Don't repeat quizzes I've already covered unless I ask.

## Optional next steps

The project is wrapped up. Portfolio presentation can come next when requested. A new model experiment, controlled user study or public release needs its own scope; none runs automatically. The timing candidate stayed unscored on audit. The separately authorised Version 3 discovery audit is now complete; those answers are exposed. Unchecked lessons can be revisited without repeating everything already covered.

## 13. Version 3: product discovery — active extension

The earlier completion statement applies to V1 and the first V2 experiment. Justin has now authorised this separate extension.

- [x] Define discovery separately from rebuying and keep the existing feature intact.
- [x] Check earlier-history availability and prepare the general-popularity ranking.
- [x] Implement and verify filtering of every shopper's previously bought products.
- [x] Build one related-product challenger and fix its settings and fallback.
- [x] Fix discovery-specific metrics and adoption criteria before scoring.
- [x] Compare methods on matching development targets and report prior answer exposure.
- [x] Review development evidence and authorise a separate reserved discovery audit.
- [x] Fix the audit plan, freeze suggestions before answers and score unchanged methods.
- [x] Verify and record audit results and mark the reserved answers as now exposed.
- [ ] Review the audit outcome together and decide the discovery prototype scope.
- [x] Build the authorised separate discovery row and check its data and interaction logic.
- [ ] Visually review and user-test discovery; don't treat offline scores as customer benefit.
