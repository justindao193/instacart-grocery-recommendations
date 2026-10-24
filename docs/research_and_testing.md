# Research and testing

No formal comparative usability experiment has been completed. Justin completed an informal walkthrough, relayed an earlier trial and supplied a transcript of one timed pilot session on 23 October 2026; details and limits are recorded below. This document separates those observations from the evidence we still need.

## What I need to learn

- How do returning shoppers decide what goes into a grocery order?
- What do they repeat, forget or deliberately change?
- What makes a suggested product useful or annoying?
- Is rebuilding a basket enough of a problem to justify this feature?

## Questions for an exploratory conversation

Ask about a recent real experience before showing a solution:

1. Tell me about the last time you ordered groceries online. How did you decide what to buy?
2. How did you remember products you'd bought before?
3. Was anything difficult or time-consuming? What did you do about it?
4. Did you use any suggestions? What made you keep or ignore them?
5. What changed between that order and the one before it?

Avoid leading with “Would an AI list help?” A positive reaction to an idea isn't the same as evidence of a recurring problem.

If I speak to people, I'll get their agreement to take notes, keep personal details out of the portfolio and record actual comments separately from interpretation. A small convenience sample can guide exploration; it won't represent all Instacart customers. This plan doesn't authorise contacting anyone automatically.

## Assumptions to check

| Assumption | Evidence available now | Next check | What might change the plan? |
|---|---|---|---|
| A useful starting list addresses a real need | Not established by this dataset | Discuss recent shopping behaviour with people | The main difficulty is unrelated to list-building |
| Earlier purchases help predict a later basket | Testable from order histories | Baseline comparison with held-back baskets | Personal history adds little useful relevance |
| A shopper can understand and use the suggestions | Informal trial reported as going fine; assistance/errors not recorded | Observe someone trying a prototype | People can't interpret the reasons or need different controls |
| Higher offline relevance saves time | Not established offline | Proposed user study or app experiment | Extra suggestions slow the task or reduce trust |

## Evidence record

| Date | Source or participant code | What was actually observed | Interpretation | Confidence and limits | Decision affected |
|---|---|---|---|---|---|
| 22 October 2026 | Justin, project owner; self-reported walkthrough | Tried the Hide task while unknowingly viewing Shopper C, couldn't find the three-dot menu, then realised the selected shopper was different. Otherwise said it felt fine. | The active example and the reason Hide is unavailable may be too easy to miss. | One project-owner report, no independent observation, timing or generalisation to grocery shoppers. | Added an active-shopper label near suggestions, a no-history explanation and a shortcut to Shopper A. Retest pending. |
| 22 October 2026 | Trial relayed by Justin; participant details not recorded | After the suggested add/hide/restore task, Justin reported “they did fine.” He also said the updated prototype looked good. | Encouraging initial feedback; specific completion, assistance and error details still need clarification. | Reported through Justin, not directly observed by the assistant. No timings or comparison; no proof of time saved or broader usability. | Keep the current design for now; ask whether the person finished without help. |

## If real user research isn't available

I'll still test the algorithm and the demo, but label the shopper problem as a hypothesis. A portfolio reviewer can test the demo's usability; that doesn't validate the needs of actual Instacart shoppers.

## Separate the questions

Offline: do suggested products match a later recorded basket?

Product value: do suggestions make shopping easier without causing unwanted purchases or reducing trust?

The first is testable with this dataset. The second needs people using a prototype or a real experiment.

## Offline comparison

Use the same labelled users and held-back baskets for each method. Start with a popularity baseline, compare personal history, then a machine-learning challenger.

The working primary metric is mean user-level Recall at 5: matched products divided by all distinct products in that user's actual target basket, averaged across evaluated users. Precision at 5 and Hit Rate at 5 provide supporting views. The definitions, cutoffs and fixed final-evaluation procedure are in [Data and methods](data_and_methods.md).

Also review differences by available history and basket size, product coverage, missing candidates and response time. Compare paired user-level score differences and report uncertainty. Define the meaningful improvement threshold and acceptable trade-offs before looking at the final scores.

If a more complex model doesn't add enough value, keep the simpler method. Documenting that decision is part of the product work.

Weighted recency is selected for version one. Final scoring is complete: allowed history inputs were refreshed, frozen ML models/scaler reused, and predictions saved before scoring final product answers. Final results are reported separately from validation in Findings and the case study. The fixed procedure remains unchanged in Data and methods. No real shopping benefit has been measured.

## Prototype feedback

I chose **time** as the main direction for testing the shopper benefit. Define it as the time from starting a consistent shopping task to adding the intended familiar products. Compare equivalent tasks with and without Buy again, account for task-order learning, and record completion, abandonment and wrong additions separately. Don't count an early exit as a successful fast task. No numeric target, test sample or experiment duration has been agreed.

Search counts can be supporting evidence if the prototype records them. The historical Instacart data doesn't contain these measures. A prototype task is a simulation and won't prove actual grocery purchase or revenue effects.

Keep Shopper A selected for the comparative task. Method explanations live in the guide, outside the shopping screen. Observe where they hesitate or misunderstand. Record what happened before deciding what to change. A simulated basket task tests the prototype, not actual purchase behaviour.

## Proposed live experiment — not conducted

Hypothesis: a relevant starting list helps returning shoppers build a satisfactory basket more easily.

If a real app and suitable instrumentation were available, assign eligible returning users consistently to the current experience or the proposed list. Define eligibility, exposure and task timing before launch.

Candidate primary outcome: basket-building time for a consistently defined task. Completion/checkout rate must be checked alongside it so faster exits aren't mistaken for easier shopping. Review cancellation or removal behaviour, unwanted suggestions and an appropriate satisfaction measure as well. Exact definitions, sample size and duration would depend on baseline behaviour and the smallest improvement worth detecting.

No experiment has been run. An offline score won't be described as a lift in revenue, retention or customer satisfaction.

## Risks and controls


For the algorithm, compare prediction scores on hidden baskets. For a future usability test, the main measure is **time to find and add the intended familiar products**, checked alongside successful task completion and wrong additions. The current dataset has no browsing, search, abandonment or feature-interaction data, so it can't measure that benefit.

| Risk | What we'll do about it |
|---|---|
| Suggestions reflect older interests | Test recency weighting; let people skip or hide a suggestion |
| People want variety or new products | Keep Buy again optional and preserve browsing/search; new-product discovery is outside Version 1 |
| We mistake a skipped item for dislike | Treat skipping as no action, not proof of a preference change |
| Faster time hides giving up or mistakes | Record completion and intended products added, not time alone |

Skip means not adding a suggestion this time; it doesn't need a separate button. Hide applies only to the exact product and remains saved for future visits in the same browser, with a way to restore it. The Hide/restore controls are implemented; feedback-driven learning is outside scope. Hide is a direct exclusion rule, not a claim that the model learns preferences from feedback.



## Still to decide

Numeric customer-benefit targets and full-app response-time requirements remain open. The first-version method choice is recorded; the small prototype pilot procedure is below. Define them prospectively before final decisions; don't claim they preceded existing validation results.


## Prototype iteration: make the active example clear

After Justin's walkthrough, the prototype now shows the current shopper above the suggestions. Shopper C explains that popular products aren't personal Buy again suggestions, so Hide isn't available, and offers “Try Hide with Shopper A.” The reviewer selector is synchronised with the page state. The ranking and Hide rules didn't change. JavaScript checks passed for the label, shortcut and shopper-specific menus; Justin hasn't retested this change yet. This is an early usability observation, not evidence of time saved.


## Small comparison test — planned protocol

**Question:** When the intended products are already in the shortlist, does Buy it again make them easier to find and add?

This is a small usability pilot, not a live A/B experiment or a test of personal relevance. Participants act as the example shopper. They aren't the anonymous customer whose order history generated the list. Tasks deliberately contain recommended products, so any speed difference applies to this favourable situation; it won't estimate the average effect across real shopping trips or missed recommendations.

### Set up two versions

- [Search and browse only](../prototype/buy_again_prototype.html?study=search): the shortlist is absent; all products, search and basket remain available.
- [With Buy it again](../prototype/buy_again_prototype.html?study=suggestions): the same catalogue and controls, with the shortlist visible.

The usual prototype link is unchanged. Test links use separate Hide storage. Open both links yourself before the session, select Shopper A, restore any hidden items through Hidden items → Show again, and reload so the basket and search are empty. Don't hide anything during timed tasks. Reload the relevant link before every task; keep the same device, window size and connection. Use a private browsing session for each participant if practical, so their test state is separate. Don't erase normal browser storage.

### Participants and task order

Start with two adults who have ordered groceries online and haven't used this prototype. Obtain agreement to take anonymous notes; no names, accounts or real purchases are needed. If only friends are available, record that convenience-sample limit. Two sessions check the procedure; they don't support population estimates. Add further participants only after reviewing this pilot, recording any revised procedure as a new round.

Use these exact product names, not a generic milk or fruit request:

| Set | Products to add | Exact product IDs |
|---|---|---|
| X | Soda; Original Beef Jerky | 196; 12427 |
| Y | Pistachios; Organic String Cheese | 10258; 25133 |

All four are in Shopper A's unhidden initial five and in the searchable catalogue. These are two-product tasks, rather than the earlier three-product suggestion, because the current example has only five recommended products. The sets aren't proven equally difficult. Do not reuse the same products across both tasks for one person.

| Participant code | First task | Second task |
|---|---|---|
| P01 | Search only, set X | With suggestions, set Y |
| P02 | With suggestions, set X | Search only, set Y |

This reverses the order and balances the product sets across conditions. With only two people, individual differences and practice effects still matter. Any additional round should reverse the set order too.

### What to say

“Imagine you're shopping for these two products. Add both to the basket using whatever you see on the page. Tell me when you're done. We're checking the design, not you. You can stop whenever you want.”

Show their assigned product list on a separate card or piece of paper. Don't point to search or the recommendations. Let them read the list, then say “Start” and begin a stopwatch. Don't ask them to explain every thought during timing; ask questions afterward.

Stop the timer when they say they're done, give up, or reach two minutes. The two-minute cap is an administrative stopping rule, not a success benchmark. Record whether the basket is correct. If they ask for help, say “Use whichever controls make sense to you.” Log the request; if you provide an instruction, log it too and classify the task as assisted. If the page breaks, record a technical failure; don't interpret it as user failure or quietly replace the run.

After both tasks ask: “Which felt easier, if either? What made it easier or harder?” Record their actual words separately from your interpretation.

### Results sheet

Leave blanks until observed. Times are seconds from “Start” to the task ending. Completion means both exact target products are present and no extra products remain. A wrong addition counts even if removed later; record whether extras remain at the end. Help includes requests and instructions, even if they ultimately finish.

| Person | Condition / set | Seconds | End: done / stopped / cap / technical issue | Correct basket? | Wrong-add actions | Extra items at end | Help requested / given | Observation |
|---|---|---|---|---|---|---|---|---|
| P01 | Search / X | | | | | | | |
| P01 | Suggestions / Y | | | | | | | |
| P02 | Suggestions / X | | | | | | | |
| P02 | Search / Y | | | | | | | |

| Person | Which felt easier? | Exact comment | Interpretation, kept separate |
|---|---|---|---|
| P01 | | | |
| P02 | | | |

### How we'll read it

Report each paired task, with completion and errors alongside time. For someone who completes both correctly without assistance, calculate search-only seconds minus suggestion seconds; a positive number means the suggestion task was faster for that person. If either task is incomplete, assisted or technically invalid, keep that outcome visible and don't report its time difference as a clean speed improvement. Don't average only successful tasks while hiding failures.

Report correct unassisted tasks / attempted tasks separately for each condition, and show wrong additions and help counts. Preserve technical failures separately. With two people, show raw observations rather than significance tests or a general percentage improvement claim. A faster task with more mistakes isn't automatically better.

**Planned pilot decision:** fix blocking confusion or errors before expanding. If tasks are completed cleanly and observations favour the shortlist, describe that as a preliminary signal in this scripted scenario and plan a larger, more realistic study. Mixed results are a reason to investigate, not to invent a pass threshold. No formal success target was agreed. The first reported session below deviated from this protocol and is recorded separately.


## First timed pilot — transcript supplied 23 October 2026

**Record R01 — first participant.** Source: a transcript supplied by Justin, not screen observation or a timer log. The actual session date wasn't independently supplied. One participant said they'd ordered groceries online and sometimes had difficulty finding products. Recruitment, prior prototype exposure and recording/note consent weren't documented in the supplied excerpt. No personal identifiers are stored here.

### What was reported

| Attempt | Task and apparent condition | Reported time | Assistance and uncertainty |
|---|---|---|---|
| First | Find “zero sugar soda” and beef jerky; context suggests search-only, but the URL/condition isn't visible in the transcript | Approximately 22 seconds | Naming clarification and moderator intervention: “Go back,” “you said sugar,” and repeated clarification of beef jerky. The exact searched text and full click sequence are unclear. Classify as assisted. |
| Second | “Now do it again”; context suggests the same products with suggestions, but products and URL weren't restated | Approximately 4 seconds | Participant had just practised finding the products. No instruction is evident during this short attempt; that doesn't independently verify unassisted correct completion. |

The facilitator treated both attempts as finished. Exact final basket contents, wrong-add actions, remaining extras, search counts, whether the basket was cleared and precise start/stop events weren't verified in the transcript. Leave these unknown; don't enter zeros or mark exact-product completion. Timing setup happened before the first “Go”; the record doesn't establish stopwatch accuracy.

The request used “zero sugar soda,” while the catalogue product is **Zero Calorie Cola**, ID 46149. This differs from planned set X (Soda, ID 196, and Original Beef Jerky, ID 12427). “Now do it again” suggests repeated products instead of switching to set Y. Preserve this as a separate pilot record; don't fill the planned P01/P02 rows as though that protocol was followed.

### Feedback and interpretation

Asked which was easier, the participant answered **“This one”** about the second version. The facilitator then asked “The 2nd one?”; no separate response to that confirmation is transcribed. Asked about difficulty finding groceries online, the participant said **“sometimes.”** No explanation of why the second felt easier was captured. This is one person's reported experience, not evidence that frequent searching is a widespread problem.

**What this supports:** the second attempt was reported as faster and the participant preferred that version. It is an encouraging observation worth following up.

**What this doesn't establish:** the suggestions caused the difference. Practice with the same items, help and wording clarification in the first attempt, unknown basket reset and unverified conditions/completion prevent a clean speed comparison. Don't turn 22 versus 4 seconds into a claimed percentage reduction, average shopper benefit or completed successful experiment.

### Next round

Keep R01; don't discard it because the procedure changed. Use a new participant and a new record. Follow the two-version links, exact names and different product sets in the planned protocol, with an empty basket before each task. Write the condition, final basket and any help alongside the time. Reverse condition order for the next planned participant to reduce the practice advantage. Ask “What made it easier or harder?” after both tasks. No interface or model change is justified solely by this transcript; first separate task-wording confusion from an actual search problem.


## Second participant — timings supplied 23 October 2026

**Record R02.** Justin clarified that the additional times belong to a second person, not corrections to R01.

| Participant | First task | Second task | Source |
|---|---|---|---|
| R01 | About 22 seconds | About 4 seconds | First participant's transcript |
| R02 | About 20 seconds | About 5 seconds | Justin's separate timing report |

Justin subsequently confirmed the order for both participants: search-only first, suggestions second. R02 used search in the first task and clicked suggested products in the second, repeating the same two products. Justin confirmed **no help was needed** and **both correct products were in the basket after each task**. These are moderator-reported confirmations, not independent screen observations.

R02's approximate times were 20 seconds using search and 5 seconds using suggestions. Exact product names, whether the basket was emptied between tasks, any extra products or wrong additions later corrected, and preference comments remain unrecorded. Correct target products being present doesn't establish zero errors or no extras. R01's help and preference aren't attributed to R02.

Both participants were reported faster with suggestions, but both encountered that condition second. Repeated products and practice remain alternative explanations; R01 also received help. Treat this as an encouraging exploratory signal, not a controlled speedup or two verified runs of the planned counterbalanced protocol.


## Version 2 offline timing test — fixed before results

This is an algorithm comparison, separate from the two prototype sessions above. The machine-readable rules are in [the fixed timing protocol](../results/v2_timing_protocol.json).

- Separate cohort: 75,000 official-test customers, using each last known prior basket as the answer and only earlier purchases as inputs. Their unknown official final baskets stay unknown. The existing dataset was previously loaded/summarised, so this isn't newly collected or guaranteed pristine unseen data.
- Customer split: deterministic SHA256 of `instacart-v2-timing-20261023:user_id`; first 60,000 are development, remaining 15,000 reserved audit. No customer overlap with the Version 1 evaluated cohort.
- Fixed baseline: Version 1's five-order-half-life weighted recency. Both methods use the same familiar candidates, targets, short-list rules and tie breaks.
- One challenger: give the baseline a bounded timing bonus, highest near the typical gap and reduced for fewer or inconsistent gaps. Typical gap is the median gap in order positions, requiring at least three earlier purchases. Sparse products get no bonus. The exact formula and constants are fixed in the protocol; no settings search is planned.
- Primary gate: at least **+0.25 percentage points mean Recall@5**, with the approximate paired 95% lower bound above zero. Precision change must be at least -0.10 points and hit-rate change at least -0.25 points. These are prospective project choices made by the assistant under implementation authorisation, not established business thresholds or industry standards.
- Report full-basket recall, matches/five precision, hit rate, history groups, short lists, timing availability and customer gains/losses. An order gap isn't a quantity or an exact calendar-time estimate.
- If development fails a gate, stop this attempt and leave audit answers unused. If it passes, save/fingerprint both audit lists before opening audit target products. Audit isn't a second opportunity to tune the rule or select settings.

Preparing features may stream the source CSV that also contains target rows, but excludes target order IDs before parsing or retaining their product IDs. Source-file hashing is for integrity, not prediction input. No automatic prototype replacement follows from an offline result; inspect complexity and evidence before adopting a change.


### First V2 development result — stopped before audit

Preparation checks passed for4,509,970 candidate rows across75,000 customers, including3,575 raw-record candidate checks from50 customers and synthetic tests for timing/fallback/cutoff behaviour. Development lists were saved before parsing that split's target product IDs. Mean Recall@5 was24.556% baseline and24.581% timing; the+0.0249-point change and approximate paired interval [-0.0027,+0.0524] didn't pass the fixed gate. We stopped, recorded the result and left audit answers unused. No revised threshold, settings search, fitted model or prototype update followed. See [development evidence](../results/v2_timing_development.json). These prediction results are separate from the human task timings above.

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

Evidence: [audit protocol](../results/discovery_audit_protocol.json), saved-prediction checks, [audit results](../results/discovery_audit.json).

## Proposed discovery walkthrough — not yet run

Use the normal prototype URL with A or B; the old study query URLs intentionally omit discovery. Ask the participant to explain the difference between Buy it again and You might also like before prompting them. Then ask them to inspect the new section and add an item only if they'd consider it for the example basket, or skip all of them. Observe understanding, hesitation, accidental additions and ability to remove an item. Ask what made a suggestion feel relevant or irrelevant. Don't define success as clicking a named visible recommendation; that only checks button use. Example histories aren't participants' own histories, so this cannot establish real personal relevance or purchase uplift. No discovery sessions have been run yet.

