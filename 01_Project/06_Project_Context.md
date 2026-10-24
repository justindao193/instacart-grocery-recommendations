# Current checkpoint

## Current UI: five discovery products — 24 October 2026

Justin requested five discovery cards. The illustrative A/B export now takes the top five from the unchanged similarity ranking; each has five unfamiliar products, all from related-product scoring, with no popularity-fill slots. C retains its popular fallback. All new cards have embedded illustrative photos, including Pub Mix and Apples. Add/remove and original study suppression passed stub-DOM checks. No browser visual review or discovery user study is claimed.

**Evidence boundary:** original development and reserved metrics remain @3. The five-card presentation is a subsequent UI scope change, not a newly validated @5 method. No evaluation scripts, frozen models, protocols or scores were changed or rerun. Audit answers remain exposed; don't imply a fresh five-item audit. Claude's portfolio copy is unchanged.

A: Trail Mix, Clementines, Crunchy Oats 'n Honey Granola Bars, Pub Mix, Apples. B: Trail Mix, Soda, Clementines, Crunchy Oats 'n Honey Granola Bars, Zero Calorie Cola. Three of five overlap. See the Learning notes for the traced explanation and limitations.

## Latest prototype update — 24 October 2026

Discovery photo placeholders replaced with embedded Trail Mix, Clementines and granola-bar stock photos, visually inspected as assets. Existing Soda photo retained. Only photo map changed; recommendation payload, CSS and code preserved. Script embed_discovery_photos.py, report discovery_photos.json and updated image source manifest saved. User asked whether five is possible; no explicit instruction to change three to five, so keep evaluated three. Explain five is a future scope change, not automatically covered by @3 results; no fresh claims from exposed audit. Browser visual review and discovery user test remain open.


## Learning checkpoint — 24 October 2026

Discovery scoring/code walkthrough completed as a taught chapter, not an assessment of mastery. Covered shared buyers, cosine equation, actual Trail Mix contribution trace, weights, exclusion/fallback, hit-rate corrections, binary matrix, nested loops, += and top3. Recap saved in existing Learning notes; dated milestone logged. Justin says reserved-test basics were already covered: skip them unasked. Next useful activity is actual discovery UI review and user walkthrough; neither is completed yet. Audit remains exposed; don't tune or rerun. No new implementation required by this lesson.


## Learning checkpoint: explain Version 3 before more implementation

23 October 2026. Justin emphasised learning and requested documentation of what/how/why. A complete V3 walkthrough now leads 04_Learning/01_Learning_Notes.md and is embedded in the guide. Covers shared-buyer similarity, baseline versus challenger, fixed rules, code/functions, audit, results, prototype export and remaining checks. Treat it as material to teach, not evidence Justin mastered it. Next explain one idea at a time, beginning with shared buyers if needed; don't automatically add another model or feature. First V3 implementation and offline evaluation are done, visual/user review still open. Audit remains exposed.


## Discovery prototype added — 23 October 2026

Justin authorised the UI extension after the reserved check. The local shopping page now has a separate “You might also like” row between Buy it again and Browse, using up to three unfamiliar items from the unchanged discovery method. Existing A/B histories personalise the saved development-fitted relationships; no target baskets are read or models refitted for the export. These are illustrative V1 example shoppers, not the audit sample.

A: Trail Mix, Clementines, Crunchy Oats 'n Honey Granola Bars. B: Trail Mix, Soda, Clementines. C retains its popular section with no duplicate discovery row. Add/toggle/remove use the existing basket. Familiar-item Hide remains unchanged; discovery doesn't have Hide in this first UI iteration. New products use neutral placeholders unless an embedded photo already exists. Source names are retained; display categories are simplified.

The original V1 study URLs suppress discovery and retain their original browse/search catalogue. CSS, old photos, Buy again data and hidden-item storage keys are unchanged. The pre-discovery HTML is archived at 99_Archive/02_Prototype_Revisions/buy_again_before_discovery.html. Claude's portfolio site/copy wasn't edited.

Checks passed in a Node VM with a stub DOM: A/B exclusions, Add/toggle/remove event handlers, search, familiar Hide separation, C, loading/error suppression and original study conditions. This isn't browser visual review, accessibility certification or user testing. Export/check reports: 05_Results/03_Checks/discovery_demo_export.json and discovery_prototype_checks.json. Exporter: 03_Code/05_Prototype/export_discovery_shoppers.py. Next: review the actual page, then test whether the new row is understandable and useful; no further model tuning on exposed audit answers.


## Current checkpoint: discovery audit complete — no tuning

23 October 2026. Justin explicitly approved the final discovery check and requested record updates. Added separate evaluate_discovery_audit.py with prepare/score stages, keeping frozen development code intact. Separate protocol fixed before audit product answers. Reused unchanged development neighbour table and popularity; no refit or audit history contribution to shared fitting. Saved 90,000 total predictions first. Independent ranking100users, raw CSV answer/match100users, cohort/exclusions and hash checks passed.

15,000 audit shoppers: hit6.626667%popularity/7.726667%related; precision2.351111%/2.737778%; novel-only recall1.785959%/2.196725% on12,253 (2,747 no-novel). Hitgain1.1pp CI[.692779,1.507221]; fixed gate passed. Hit gains/losses/ties569/404/14027; net165. Coverage25/1444;18 fallback slots; no short lists. Reports discovery_audit_protocol.json, discovery_audit_preparation.json, discovery_audit.json; saved lists discovery_audit.sqlite.

AUDIT NOW EXPOSED. No tuning or fresh-test claims on these baskets. V2 timing remains stopped and unscored on audit; V3 discovery was separately authorised. Prototype and Claude portfolio site unchanged. Notes/log/path/brief/research/findings/decisions/canonical case study and saved-result notebook updated. Next discuss building a separate discovery section and appropriate user testing; user hasn't yet reviewed this result or authorised a UI build in this audit turn. Earlier statements that reserve is unused are historical.

## Current checkpoint: first discovery result ready to discuss

23 October 2026. Justin said proceed with V3. Implemented evaluate_discovery.py; single fixed co-buyer cosine attempt, support>=50 buyers, overlap>=5, top40 neighbours, top10 recency-weighted personal seeds, exclude full personal history, top3 and popularity fill. Frozen discovery_protocol.json before task-specific answer read; both lists saved first in discovery_development.sqlite. Development reused V2's exposed 60k customers. Hit6.563333%baseline/7.776667%related; precision2.296111%/2.766111%; novel-only recall1.815633%/2.197270% on49118,10882 no-novel baskets. Hitgain1.213333pp CI[1.011031,1.415636]; agent-selected gate passed. Coverage25/2705 products;135 fallback slots; no short lists. Detailed report discovery_development.json and verification discovery_verification.json.

No audit records or answers used, no V1/prototype/portfolio edits. Additional independent reranking100randomusers and whole-output exclusion checks pass. Saved Recommendation methods notebook preview reads reports without recomputing. Next explain the comparison simply and discuss a separate fixed audit protocol; don't automatically score reserve, tune settings, announce a final winner or claim causal benefit. Older “not built yet” checkpoints below are historical.

## Current checkpoint: Version 3 discovery started

23 October 2026. Justin approved the new-product discovery extension. V1 remains the completed Buy again prototype, V2 remains the stopped timing attempt, and V3 replaces the earlier future “learn from use” placeholder. Portfolio drafting by Claude is preserved; don't change that site or claim discovery is delivered there.

Defined scope and proposed evaluation in Project brief. Prepared history-only popularity ranking: 47,352 products / 876,349 orders / 8,838,134 lines / 60,000 development customers. Script prepare_discovery_baseline.py; discovery_preparation.json report; discovery_popularity.sqlite output. No target answers or audit records used by this preparation; no UI change or discovery scores. Development answers are already exposed from V2. Next build/check unseen-product filtering and a related-product challenger, freeze its scoring choices, then compare on matching development baskets. Reserved audit stays untouched. Version 3 is active, not complete.

## Current status: portfolio case study drafted

23 October 2026. Following the portfolio handoff, Claude built the Buy it again case-study page on Justin's portfolio site (instacart.html, with a prototype copy, film and clips under instacart/). It uses only recorded evidence and keeps the independent-project note, the pilot limits and the Version 2 stop visible. The analysis, prototype, models and scores are unchanged. Next: Justin reviews the page wording; public hosting and an asset/branding review are separate decisions. Earlier checkpoints below are historical.

## Current status: learning project wrapped up

23 October 2026. Justin asked whether the project was done, then authorised updating the learning records and related documents. The checked analysis, local HTML prototype, exploratory pilot records and standalone case study form the completed learning-project scope. Added the V2 outcome to the case study and a concise end-to-end recap to Learning notes. Weighted recency stays selected; the first V2 timing rule stopped at development. No further model run, audit scoring or UI change is needed to finish this scope.

The 15,000-person audit remains unscored. Don't tune the saved V2 attempt or reopen V1's exposed holdout. Future research, independent reproduction, full app/accessibility checks, hosting and portfolio presentation remain separate work. Unchecked exercises aren't claims of completed learning; browser-local task state hasn't been overwritten. Next, help with portfolio presentation or a requested refresher rather than automatically starting another version. Earlier checkpoints below are historical.

Updated: 23 October 2026.

## Current checkpoint: first V2 timing attempt stopped at development

Justin said go for it after scope explanation, explicitly preferring action over repeating gap basics. Added03_Code/03_Model_Comparison/evaluate_purchase_timing.py. Fixed protocol before results: deterministic60kdev/15kaudit from75k disjoint V1 evaluated users; last known prior targets, earlier-only inputs; median purchase gap/MAD with>=3 earlier purchases; bounded bonus to unchanged recency, sparse fallback; no model fit/settings search. Gate+0.25pprecall, paired lower bound>0, precision>=-0.10pp, hit>=-0.25pp; assistant-chosen project criterion, not business-agreed/industry standard.

Preparation passed4,509,970 candidates,11,011,698 history lines;50 raw-sample users/3575candidates, value/cutoff checks and300 synthetic-history checks. Split:dev3,618,144 candidates/840010timing-available; audit891826/206710. Targets excluded before product-ID parsing in preparation. DB02_Data/02_Prepared/v2_timing.sqlite. Frozen protocol/prep reports under05_Results/03_Checks.

Development60000: precision37.302333%baseline/37.374%timing; recall24.555852%/24.580704%; hit79.56%/79.556667%. Recall+.024852pp, approx paired95%[-.002718,+.052422], gatefalse. More/equal/fewer2028/56137/1835;1580shortlists each;20731changed ranked lists. Saved lists before reading dev target IDs. Audit guard checked and refused; no audit predictions/report or target scoring. Stop fixed attempt, leave15k reserve unscored, retain V1 prototype. Reportsv2_timing_development.json; outputsprivatev2_timing_development.sqlite. Existing dataset previously loaded/summarised, not guaranteed pristine unseen source; don't compare V2 values directly to V1 finals.

Brief/path/learning notes/log/findings/decisions and saved-report notebook updated. Next explain this actual result simply and review why a plausible clue added little; don't tune constants, run blocked audit, claim all timing fails or change UI automatically. Any later experiment needs a new disclosed plan acknowledging inspected development answers. V1 code/models/results/frozen plan and case study remain intact.

### Previous checkpoint: Version 2 purchase-timing feasibility checked

Justin explicitly wants Version2 before wrapping up/portfolio packaging. Recommended testing purchase timing, and he agreed to check the roadmap/data. Metadata-only scan of orders.csv plus V1 evaluation_plan confirmed75000 official-test customers disjoint from131209 V1 customers, each with2–98 earlier orders before their last known prior basket. That known prior basket can be a new retrospective target; official final test contents remain unknown. History groups26662/26199/22139. No product contents read for this check. Existing source was already broadly loaded/summarised, so don't call this newly collected or pristine unseen data. No later known baskets after V1 finals were obtained.

Brief/path now plan order-gap timing for familiar products; minimum3 earlier purchases gives2 observed gaps, with missing/reliability handling and baseline fallback. Proposed60000development/15000audit customer split not yet created; rule/settings/adoption criterion not agreed. Keep V1 outputs/prototype/frozen plan unchanged. Next tutor one simple gap example and agree the rule/plan before building or scoring. Don't build ahead of the lesson, claim V2 gains, retune on V1 final answers or proceed to portfolio packaging. Feasibility record:05_Results/03_Checks/v2_feasibility.json.

### Previous checkpoint: final case-study narrative review complete

Justin authorised the final case-study review on23October. Updated the summary to reflect completed offline work and both pilot sessions; added explicit model-choice trade-offs and a separate two-person usability table. R01 about22s/4s, search assistance and preferred second; R02 about20s/5s, no help, both correct targets present. Both search first and repeated products: no causal speedup, no zero-error claim or percentage lift. Separated completed deliverables from full app timing, independent setup, fuller UI/accessibility checks and hosting. Kept supplied screenshot, sources and AI assistance; updated Findings for consistency. Final metrics/intervals checked against saved reports, links/image paths and guide scripts checked. No app/model/data changes or new test claimed. Portfolio packaging and deployment remain later work; don't restart model lessons or repeat completed basic interaction checks. Next prepare a shareable package only within explicitly authorised scope, without publishing automatically.

### Previous checkpoint: desktop screenshot saved and added

Justin supplied a real desktop screenshot on 23 October: Shopper A, five Buy it again products, Soda marked Added and Soda in Basket. Copied it unchanged to 01_Project/Assets/screenshots/01_buy_again_desktop.png and embedded it with factual alt text/caption in the case study. README/checklist updated for this specific capture, not all screenshots. Guide refresh now resolves image src paths as well as links; screenshot CSS keeps it within the article. No generated screenshot, page automation or prototype/model changes. Basic layout/keyboard already reported working; don't repeat. Full app timing, independent setup and remaining release checks stay open.

### Previous checkpoint: local setup and link review complete

On 23 October reviewed README, code map, launchers, workspace and dependencies. All99 pre-edit active Markdown/HTML file links passed;100 locked package versions match and pip check passed. Improved README to distinguish browser-only prototype, full local guide and analysis prerequisites. Setup now selects Python3.13 and reuses existing environment; old preparation launcher checks DuckDB import before starting and explains the historical route if blocked. Refresh launcher returns an error on failure. No setup/install, Jupyter server or data/model rebuild was run. Clean-machine reproduction, full app timing, remaining UI/state checks, screenshots and deployment remain open. No need to repeat basic owner-tested interactions/layout/keyboard. See setup_review.json for local checks. Next complete remaining technical evidence or review case study; public sharing requires separate preparation. User prefers short explanations.

### Previous checkpoint: basic layout and keyboard checks reported working

On 23 October Justin said the narrow-window layout check worked and confirmed the basic Tab/Enter keyboard check worked. Prompted scope was search, Add and Basket, visible focus and moving away from controls. These are owner-reported basic checks, not an assistant-observed browser test, physical-phone test or full accessibility audit. Checklist updated for those two checks; remaining controls/states and full performance/setup remain open. Don't repeat these basic walkthroughs. Next check setup/run instructions without rebuilding frozen data/models. No prototype changes.

### Previous checkpoint: two pilot sessions, R02 details confirmed

Justin reported R01 about22s search then4s suggestions; R02 about20s search then5s suggestions. He confirmed both did search first. R02 repeated the same two products, searched first then clicked suggestions, needed no help, and both correct products were in the basket after each task. Exact R02 product names, basket reset, extras/corrected wrong additions and preference aren't recorded. Don't infer zero errors or copy R01's feedback. R01 transcript included naming clarification/help and preference for second; final basket/reset weren't confirmed for R01. Both second tasks were faster, but repeated products/fixed order and R01 help prevent a causal time-saving claim. Research, case study and log reflect these boundaries. No more basic controls walkthrough needed. Next review this exploratory evidence and finish remaining technical checks; a stricter future test should vary task sets/order and record basket reset/errors. No prototype/model changes.

### Previous checkpoint: code organised by project stage

Justin asked for consistent grouping and naming. Working code is now under 03_Code/00_Run, 01_Data_Preparation, 02_Baselines, 03_Model_Comparison, 04_Final_Evaluation, 05_Prototype and 06_Guide. Python and SQL use snake_case; queries stay with their related scripts. See 03_Code/README.md for the map. Updated active paths, Python project-root lookups, cross-folder model import, batch launchers, notebook sources and guide links. Prototype is now 03_Code/05_Prototype/buy_again_prototype.html. Data, models and saved predictions/reports stay in place. Frozen hashed code preserved byte-for-byte in 99_Archive/03_Frozen_Evaluation_Code; protected plan unchanged. Historical notebook outputs and frozen plan retain original paths. No models rerun or final answers reopened. Next resume the prepared pilot; no results yet.

### Previous checkpoint: comparison pilot prepared

Justin confirmed the basic prototype interactions have already been checked and work; don't repeat that walkthrough. He authorised preparing the next benefit test. Research and testing now contains a two-participant, order-balanced, two-product comparison with exact tasks, facilitator script, timing/error/help definitions and blank results. Optional ?study=search removes the shortlist; ?study=suggestions includes it, with separate test Hide storage. Normal prototype unchanged. Tasks deliberately use relevant recommendations, so this tests findability under favourable conditions, not personal relevance or real shopping-time benefit. No participants contacted, results collected or test claimed complete. Next Justin runs P01/P02 and supplies observations. Browser local-file restriction still applies; don't bypass it.

### Previous checkpoint: standalone case study, portfolio later

Justin clarified that the current deliverable is a strong standalone case study. Portfolio presentation comes after the remaining project work. Reworked 01_Project/05_Portfolio_Case_Study.md around the problem, scope, data preparation, evaluation design, five-method comparison, final results, recommendation, implementation, risks and next validation. Removed the portfolio introduction and resume bullet. Existing filename retained to preserve links. Reporting structure draws on Microsoft's data-science lifecycle and Nielsen Norman Group's evidence-led reporting guidance, linked in the report; no claim of certification or a universal industry template.

Final figures and uncertainty come from saved reports. Weighted recency was selected before final scoring; the report acknowledges the tree accuracy advantage and keeps informal feedback separate from measured customer benefit. Authorship and AI assistance are explicit. No model, prediction, prototype or research changes were made for this editorial revision. Guide refreshed; browser task state isn't claimed synced.

Remaining: actual-page screenshots, fresh full desktop/mobile/keyboard review, full app response timing, independent setup check, structured product-benefit testing and deployment preparation. Local file URL remains blocked by the browser tool; don't attempt a workaround. Nothing deployed. Don't repeat completed model-selection lessons or retune against the inspected final holdout. Finish or review the outstanding checks before portfolio packaging. Earlier sections below are historical checkpoints.

## Latest: official logo, carrot tab icon and problem wording

Justin defined the goal as helping shoppers find wanted products with less searching. Saved a concise first-person problem section in the existing portfolio outline, specifying familiar products and that reduced effort remains a hypothesis. User requested actual Instacart logo instead of typed text, and carrot for the browser tab (screenshot showed generic globe). Embedded unmodified full-colour dark SVG from the public instacart.ca header asset; saved03_Code/05_Prototype/assets/instacart_logo.svg. Added embedded PNG favicon from the official public brand-site carrot. Both source hashes/URLs recorded in existing image manifest; helper updated to preserve these on future image restoration. Verified official remote SVG visually, local embedded bytes against sources, and unchanged CSS/complete shopping JS. Local page browser-tool restriction remains, so ask Justin to refresh Ctrl+Shift+R; no workaround attempted. No model/data changes. Continue portfolio story next; no claim of measured time saved.

## Current UI decision: shopping only

Justin explicitly requested removal of Try it/Compare methods/About and demo explanations, with simple Hide wording. Prototype now has the shopping page, embedded photos/carrot, search/browse, Basket and a compact A/B/C selector. Removed portfolio tab content, reviewer/state/reset bar, demo labels and explanatory/footer credit text; sources remain in project files. “Hide” and “[Product] hidden” replace long copy; Show again/Undo unchanged. Independent-project limits and methods stay documented outside the shopping interface. Don't reintroduce the removed tabs, reviewer bar or tutorial banners. Updated requirements, brand guide and lasting AGENTS preference. JS checks passed for remaining controls with missing-element detection. Data/photo payloads unchanged. Browser file-URL restriction remains; human visual review pending. No new model/research claim.


Latest refinement: moved shopper control beside search instead of the far-right auto margin; replaced the square native popup with a rounded custom A/B/C menu. Keyboard arrows, Enter/Space via buttons, Escape and outside-click dismissal supported. Empty basket now says “Your basket is empty. Add an item to get started.” Removed the Photos from Unsplash footer as requested; source records remain. Code checks passed for selector state/focus, A/B/C lists, Add/remove and Hide/Undo. No data/model changes. Justin's visual review is next.

## Latest feedback: informal trial

Justin said the photo-restored prototype looked good. After the proposed task for another person (add two products, hide one, bring it back), he reported “they did fine.” Recorded the report with its limits in Research and testing and Learning log. No specific help/error/timing details supplied. Don't claim an independently observed pass, zero errors or time savings. Next ask whether they finished without help. Keep the design; no new implementation requested.

## Latest update: photos and carrot restored

Justin requested both product pictures and the carrot logo after supplying Claude's handoff. Read the current requirements, brand guide and newest log; earlier handoff requests for sample-to-real export were already completed. Added restore_prototype_images.py and embedded images for all 19 real A/B candidates (17 previously missing entries). Retained original stock photos; new photos are illustrative product types rather than exact branded items. Source/license references and hashes: 01_Project/Assets/prototype_image_sources.json. Unmodified official public brand-site carrot asset is embedded beside plain-text instacart and saved as03_Code/05_Prototype/assets/instacart_carrot.png. CSS and recommendation data unchanged. Code checks pass for image references, lists, Hide replacement and fallback. No new model work or final-answer access. Guide refreshed with task scripts preserved.

Browser tool rejected the local file URL under its security policy; don't work around that browser restriction. Justin should refresh his existing Chrome tab for visual review. No claim of browser screenshot QA or completed usability testing for this change. No added shopper banner. Prior sections below describe earlier stages.

## Current prototype: real data, approved design retained

Codex adapted export_demo_shoppers.py to integrate real A/B summaries into Claude's approved HTML without changing its existing CSS, embedded photos, broad browsing categories, layout or controls. No active-shopper banner/shortcut added. Styles and photo block verified unchanged from immediately before this integration; the Downloads reference wasn't edited. Main page: 03_Code/05_Prototype/buy_again_prototype.html. A: user 1, 10 earlier orders/18 candidates; B: user 113, five earlier orders/one candidate; C explicitly simulated no-history. Full candidate lists support Hide replacements. First lists match frozen weighted-recency predictions; zero order positions since purchase means Last order. New candidates without photos use placeholders. Existing display groups are broad demo categories, not exact source aisles. Data export and report refreshed in existing locations. No target answers, model refits, scoring or frozen-prediction changes.

JavaScript checks passed for lists, Hide replacement/all-hidden, restore eligibility, per-shopper storage, tags and basket add/remove. These are code checks, not human usability or browser visual checks. Next: Justin reviews the project copy in Chrome, not the untouched Downloads sample version. Keep the approved design; gather feedback before changing presentation. No deployment or app-framework migration.

## Historical design rollback

Justin rejected Codex's earlier modified presentation and preferred Claude's Downloads version. That file was restored before this minimal data integration. Prior banner/data revision is archived in 99_Archive/02_Prototype_Revisions. Earlier entries below describe historical stages and don't override the current state above.

## Latest prototype feedback

Justin completed an informal walkthrough: felt fine overall, but tried Hide while unknowingly on C and couldn't find the three-dot option. Recorded actual report in Research and testing; not independent usability research or a timing test. Added an active-shopper label near suggestions, C's missing-Hide explanation and a “Try Hide with Shopper A” shortcut. Selector and page state now synchronised. JavaScript checks passed; Justin's retest is next. No ranking changes.

## Prototype: real example data connected (22 October, Codex)

Current prototype: 03_Code/05_Prototype/buy_again_prototype.html. Current design requirements: 01_Project/07_Prototype_Requirements.md. Claude built the HTML shopping experience; Codex connected two real anonymous historical examples with export_demo_shoppers.py. A: 10 earlier orders, 18 familiar candidates. B: five earlier orders, one familiar candidate. C is explicitly simulated no-history, not a measured new-customer example. Full candidate lists allow Hide replacements; initial top-five lists exactly match frozen weighted-recency predictions. Data is embedded so opening HTML needs no server. Local export: 02_Data/03_Model_Outputs/demo_shoppers.json; check report: 05_Results/03_Checks/demo_shopper_export.json. No final answers read, refit or frozen prediction changes.

Latest-order tag corrected to orders_since_last_purchase == 0. Exact source names/aisles replace sample catalogue labels; existing stock photos retained, other products have placeholders. Hidden state uses a new real-v1 browser key so old sample exclusions don't carry into these examples. Code-level JavaScript checks passed for initial lists, hide/replacement/all-hidden, restore eligibility, per-shopper storage, tags and basket add/remove. These aren't browser visual checks, real browser persistence tests, accessibility audits or human usability tests. No deployment. Web HTML prototype is current; Streamlit/custom-web architecture remains undecided and Figma optional.

Next: Justin opens/refreshed prototype in Chrome, tries Shopper A Add/Hide/Undo, Shopper B short list and simulated C fallback, then reports confusing behaviour. Later agree usability tasks and record actual observations. No claim of saved shopping time. Guide refreshed from canonical Markdown with task scripts preserved.

## Version-one decision: selected

Justin explicitly chose weighted recency as the first demo's default on 22 October and asked for a first-person iteration record. Recorded it in 05_Results/02_Decisions.md, summarised in Learning notes, added the authorised approach/recommendation sections to the portfolio outline and updated Project brief/path. Final scoring is now complete below; no app yet. Don't ask him to choose the method again.

Selected rule: sum 0.5 ** ((eligible_history_cutoff_order - purchase_order_number)/5) per customer/product, round total to12decimals; score descending, latest purchase order descending, product ID ascending. Top5distinctfamiliar products; fewer if insufficient candidates, no discovery filler. Exact-product Hide/restore planned before top5, same-browser storage; app controls aren't built. General popularity fallback for nohistory is planned and untested for new customers. ML challengers retained for the planned comparison view, not default suggestions.

## Why this choice

Tested five approaches, not every possible model: popularity→personal frequency→weighted recency→logistic regression→boosted trees. Same131209validationcustomers/targets. Mean Recall@5:4.714%,23.441%,24.543%,24.546%,24.707%. Popularity candidates can be unfamiliar; other methods are rebuy-only. Personal ML inputs: purchase count/share, orders since last purchase, fixed recency score, history length. Logistic uses training-only scaler/L2 C1. Tree uses100smallrounds,lr0.1,maxleaves15,depth4,minleaf100,L2=1,noearlystopping,seed0. One fixed attempt each, no setting sweep.

Trees genuinely improved validation recall by+.164pp (approxpaired95%+.136to+.192 under independent-user assumptions), below proposed working+.5pp target introduced before the tree result, after earlier validation. Not an industry rule or pre-registered general business criterion. Justin prioritised explanation/maintenance over this modest gain, not maximum measured accuracy. No unsupported claim that trees are slow or ML can't help.

Customer outcomes vsrecency:6794morematches,119054samecount,5361fewer. Coverage(weighted/logistic/tree):29138/29128/29271 distinct products out of49371eligible; top10slotshare11.31/11.32/11.18%; all3521shortlists and648697slots. History/basketgroups reviewed. All3fast locally:medians0.00535/0.2044/0.5409ms on preparedinputs, savedlistretrievalabout0.041ms each. Warm90userbenchmark excludes rawfeatures/startup/network/UI, isn't app latency. More coverage isn't automatically better; equal matches needn't mean same lists.

## Data and runtime

SQLite current:02_Data/02_Prepared/instacart_ml.sqlite, ml_features; features_checked marker passed. DuckDB still blocked by Windows Smart App Control; no security settings changed. Historical DuckDB files retained, old notebook Run All still reaches blocked imports. Use project .venv/Scripts/python.exe and current SQLite routes, not old builders.

For validation order v: ML training inputs<=v-2,targetv-1; validation inputs<=v-1,targetv. One training target/customer. Training7324671rows,validation7912788. Official train baskets have now been used for the completed final check; unknown official test contents aren't empty baskets. No price/quantity/browsing/exposure data. Original CSVs unchanged.

Existing code:build_ml_features.py/ml_features.sql; shared train_logistic_validation.py and tree entry train_boosted_validation.py. compare_recency_groups.py offers --trees, --benchmark, --coverage,--basket-size SQLite diagnostics. Check reports in05_Results/03_Checks. Local models/details in02_Data/03_Model_Outputs, ignored byGit. Grouped notebooks have saved-report previews that run independently of old DuckDB cells.

## Next step and limits

Fixed final-evaluation procedure is now documented in 01_Project/03_Data_And_Methods.md, before execution. Same131209cohort; final inputs through final_history_max_order_number, target final_target_order_id. Former validation basket may be earlier final history. All5fixedmethods compared; primaryselectedweighted vsfrequency, others reported. ML comparators/scaler frozen as originally learned, no refit. Save and audit predictions before opening final product answers. Existing metric/group/coverage rules and approximate paired intervals fixed. No new tuning or winner selection against final results. If evidence is weak, disclose and require fresh holdout for iteration.

Prediction-only stage is now complete:03_Code/04_Final_Evaluation/prepare_final_predictions.py +final_features.sql. Frozen artifact02_Data/03_Model_Outputs/final_predictions.sqlite, report05_Results/03_Checks/final_prediction_preparation.json statuspassed. Contains targets,8474661final-historyfeature rows and3262685predictionrows across5methods/131209users. No final answer/score tables. Popularity656045slots/0shortlists; all4personalmethods651660slots/2168shortlists. Finalhistoryorders2047377. Reduced short lists reflect one more known basket, not ranking improvement.

Checked source hashes vs prepared report, final target metadata/order sequence, cutoff-safe features, unique/eligible lists, frozen ML model files/state and independent raw-history features plus independently sorted rankings100users. Synthetic SQL test excludes final target products. Initial empty-file connection attempt failed on URI handling; removed only inspected empty artifact, corrected URI and successful build passed all checks. SQLite connection explicitly closed before freezing Windows file. Completed in117s, not app latency.

Final scoring is complete and passed. New03_Code/04_Final_Evaluation/score_final_predictions.py verifies predictions/source/models/code/plan fingerprints before answers, opens original final CSV once for scoring, writes separate final_scores.sqlite and final_evaluation.json. All131209users,1384617finalproductlines. No new inference/refit/ranking changes. Prediction hash verified unchanged before/after. Score script refuses overwriting an exposed run; frozen plan retained unchanged for provenance.

Final precision/recall/hit(%):popularity9.47755/4.68716/36.24218;frequency35.40596/23.11600/78.23091;weighted37.31970/24.27597/79.37489;logistic37.29516/24.27866/79.38023;trees37.57669/24.45232/79.44958. Primary weighted-minus-frequency recall+1.159976pp,approxpaired95%[1.112438,1.207514]. Trees-minus-weighted+.176344pp[.147776,.204912];logistic+.002686pp[-.016818,.022190]. These aren't live benefits. Selected default remains weighted per pre-final decision; don't reselect after final answers.

All5exactcohort/targets/sizes verified; independent100users/method rawCSVsetoverlap; valid bounds; fixed history/basketgroups and slots reconcile. Final personal shortlists2168,slots651660; pop656045. Group historycounts38076/51519/41614,actualbasketcounts39359/39002/38409/14439. Coverage pool49468;weighted28721,logistic28749,tree28973distinct. Detailed answers/scores localignoredGit at02_Data/03_Model_Outputs/final_scores.sqlite; aggregate final_evaluation.json inChecks. Preparation report's final_answers_readFalse describes its earlier prediction-only stage, not current global status.

Next: teach/interpret final results with Justin, then sketch/build Streamlit with the fixed weighted default. No app building in this scoring turn. The holdout is NOW EXPOSED: do not tune against it, rerun as a fresh test, or change models silently. Future iterations require fresh holdout/newdata. Business findings/case-study remainder still joint work.

Uncertainty interpretation can be refreshed if needed; don't claim independent mastery or repeat basic quizzes unasked. Numeric prototype acceptance criteria, user research, app build, live benefit evidence and full portfolio completion remain open. No business findings or imaginary interviews.

## Teaching and records

Use simple casual language and explain technical terms/tools. Justin requested and received a full and simplified code-flow explanation; he now says he understands. One idea/check at a time, save at concept/milestone boundaries rather than every answer. Current choice write-up is first person and honest about AI-assisted implementation. Keep five active folders/three grouped notebooks, simple Learn path/notes layout and task-state compatibility. Learning path is updated; browser-local task statuses aren't automatically synced. Refresh HTML after Markdown edits.
