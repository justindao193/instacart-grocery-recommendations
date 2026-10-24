# Code map

Folders follow the project stages. Folder numbers give the order; Python and SQL filenames use snake_case. Keep related queries and scripts together. A number isn't an instruction to rerun completed work.

| Folder | What it does |
|---|---|
| 00_Run | Setup, notebook and guide shortcuts; dependency lock; VS Code workspace |
| 01_Data_Preparation | Download, prepare and verify data; introductory SQL practice |
| 02_Baselines | Popularity, personal frequency and weighted recency; their SQL and scoring |
| 03_Model_Comparison | SQLite ML features, shared model runner, tree entry point, validation diagnostics and the Version 2 timing study |
| 04_Final_Evaluation | Prepare frozen final predictions and score them separately |
| 05_Prototype | Buy it again page, example exporter, image helper and assets |
| 06_Guide | Refresh the project guide from its Markdown documents |

Start the app with [buy_again_prototype.html](05_Prototype/buy_again_prototype.html). Opening it doesn't run Python or train a model. Optional comparison links are documented in [Research and testing](../01_Project/04_Research_And_Testing.md).

Run Python with the project interpreter from the project root, for example:

```powershell
.\.venv\Scripts\python.exe .\03_Code\06_Guide\refresh_guide.py
```

The tree entry point reuses train_logistic_validation.py in the same folder. The final prediction script explicitly imports that shared runner from 03_Model_Comparison. SQL paths and notebook source cells follow this layout.

The original DuckDB routes are retained and can still hit the known Windows module block. Current ML feature preparation uses SQLite. Organisation doesn't make those old routes newly runnable.

## Completed evaluation evidence

Don't rerun final evaluation to overwrite the inspected holdout. Data, models, predictions and generated reports weren't moved or rewritten. Original hashed code is preserved under 99_Archive/03_Frozen_Evaluation_Code; the scoring integrity checks resolve historical paths there. The frozen Data and methods plan and old notebook outputs keep historical paths as evidence. Current commands and notebook source cells use the new paths. The move map is in 05_Results/03_Checks/code_organisation.json.


## Version 2 timing workflow

`03_Model_Comparison/evaluate_purchase_timing.py` has four explicit commands: `self-check`, `prepare`, `development`, and `audit`. It writes separate `v2_` files, never overwrites existing results, and refuses audit if development fails the fixed gate. Preparation uses SQLite and earlier history only. The fixed settings and split are recorded in `05_Results/03_Checks/v2_timing_protocol.json`; don't edit the evaluated code or protocol to disguise a later settings change. No full-source rebuild or V1 model rerun is needed.

### Discovery preparation

`03_Model_Comparison/prepare_discovery_baseline.py` reads only development histories from the existing checked SQLite database and saves a popularity ranking to `02_Data/02_Prepared/discovery_popularity.sqlite`. It refuses to overwrite existing outputs. The report is `05_Results/03_Checks/discovery_preparation.json`. This is preparation only: per-shopper exclusions, related-product recommendations and scoring aren't implemented yet.

### Discovery development comparison

`03_Model_Comparison/evaluate_discovery.py` fixes its protocol, builds shared-buyer product links from development history, saves unfamiliar top-three lists, then scores development targets only. It refuses overwrites and has no audit command. Outputs: `02_Data/03_Model_Outputs/discovery_development.sqlite` and aggregate `discovery_protocol.json`, `discovery_development.json` under Checks. `discovery_verification.json` records additional read-only reranking/exclusion checks. Don't edit frozen code or rerun to overwrite the inspected attempt.

### Reserved discovery audit

`04_Final_Evaluation/evaluate_discovery_audit.py prepare` freezes a separate protocol and saves audit suggestions using unchanged development neighbours and popularity. Its `score` stage checks hashes before parsing only audit targets and independently verifies a raw CSV sample. Both stages have overwrite guards. The authorised run is complete; don't rerun it as a fresh test. Reports are `discovery_audit_protocol.json`, `discovery_audit_preparation.json` and `discovery_audit.json`; private saved lists are `02_Data/03_Model_Outputs/discovery_audit.sqlite`. The V2 timing audit was not run.

### Discovery prototype export

`05_Prototype/export_discovery_shoppers.py` reads frozen discovery relationships and existing A/B history features, exports three unfamiliar items into the HTML and records `discovery_demo_export.json`. It doesn't read target answers or refit models. Existing photos are reused; missing images use neutral placeholders. Run it after any intentional refresh of the base example catalogue. Logic-check evidence is in `discovery_prototype_checks.json`.

### Five-card presentation update

`export_discovery_shoppers.py` uses `DISPLAY_COUNT=5` for illustrative A/B UI exports and saves per-item contributions in `discovery_demo_export.json`. Existing frozen evaluation remains @3. `embed_discovery_photos.py` embeds the new cards' illustrative photos; source hashes/licenses live in the image manifest. No evaluation rerun is needed for this UI export, and current @3 metrics mustn't be relabelled @5.
