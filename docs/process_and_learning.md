# Product process and learning

This was solo, AI-assisted work. I used a lightweight local task board and milestone-based notes rather than a formal team sprint process.

| Stage | Question and decision | Evidence |
|---|---|---|
| Define | Help returning shoppers reach familiar products; keep checkout, accounts and live inventory outside scope | [Project brief](project_brief.md) |
| Establish baselines | Compare popularity with personal frequency, then weight recent purchases | [Case study](case_study.md), [baseline code](../src/baselines/) |
| Challenge the rule | Test logistic regression and boosted trees; accept a small accuracy cost for an inspectable V1 rule | [Decision log](decision_log.md), [final results](../results/final_evaluation.json) |
| Stop an idea | Timing didn't clear its pre-result development criteria; don't quietly move the threshold | [Timing result](../results/v2_timing_development.json) |
| Extend carefully | Separate unfamiliar discovery from rebuying; use shared-buyer product links and a reserved comparison | [Discovery audit](../results/discovery_audit.json) |
| Match product scope | Expand illustrative discovery to five; label its later exposed-data measurement honestly | [Top-five report](../results/discovery_top_five.json) |
| Learn from people | Record two exploratory find/add sessions, assistance and practice limitations | [Research record](research_and_testing.md) |

The task board tracked IDs, priority, dependencies, completion criteria and notes in Doing, To do, Blocked and Done columns. A separate learning path, dated milestone log, decision record and context checkpoint kept implementation and lessons organised. The full local board and lesson transcripts aren't needed in this public repository; they aren't proof of formal Scrum delivery or independently mastered skills.

I learned to distinguish customers from orders/product lines; prevent later answers entering recommendation inputs; compare ranking methods on matching baskets; distinguish precision, recall and hit rate; and inspect how personal recency and shared-buyer similarity contribute to suggestions. Explanations and worked examples were assisted by Codex. Claude helped design the prototype and portfolio. My role included scope decisions, comparison review, trade-offs, design feedback and facilitating exploratory sessions. I don't claim independent authorship of every code block.

A useful product lesson was that a more accurate model needn't be the best first implementation, and a faster second prototype task doesn't prove a feature caused the improvement. Future price/stock/personal-preference information would need new data, not assumptions from missing purchases.

## Making the repository reviewable

After the analysis, I added a small runnable reference of the selected rules, an invented example, behaviour checks and a code walkthrough with AI implementation help. This separates understanding the method from rebuilding the private analysis environment. Historical scripts and reports stay unchanged. A Windows/Linux check workflow is configured; a hosted pass is not claimed before publication.
