# Run #20 finding stability review — 2026-09-29

## What changed

Run #19 and Run #20 each cover the same 557 exact SKUs. Comparing one grade
and the set of finding codes for every SKU gives **six changes (1.08%)**:
all six are TV HIGH → PASS. No SKU was added or removed. For the other ten
families, two separately collected unified attempts produced the same
grade/finding-code pair for all **392 SKUs**.

The five `QN55/65/75/85/98LS03HEFXZA` models had
`ENERGYGUIDE_FILE_NOT_READABLE_CANDIDATE` in the previous TV artifact. Its
PDP supplied EnergyGuide URLs ending `552...pdf`, and retrieval classified
the documents `SAMSUNG_NASCA_SERVER_DRM`. Run #20 PDPs supplied different
EnergyGuide URLs ending `554...pdf`; each was accessible and its printed
model matched the PDP SKU under the approved fixed-prefix rule.

`UN43U8000HFXZA` previously had no EnergyGuide Support document and carried
`ENERGYGUIDE_DOCUMENT_MISSING_CANDIDATE`. Run #20 exposed a document URL;
its printed model matched. This is an observed **source/accessibility change**.
The evidence does not prove when the public document changed or that a
regulatory violation was permanently remedied. The dashboard should describe
the six as **current-source PASS transitions**, not final issue resolutions.

## Execution reliability is a separate risk

| Unified run | Result | Reason |
| --- | --- | --- |
| [36429133339](https://github.com/Empty-Bell/RDA/actions/runs/36429133339) | FAIL | TV shard aggregation path mismatch in orchestration; 165 PDP captures were recoverable. |
| [36434554492](https://github.com/Empty-Bell/RDA/actions/runs/36434554492) | FAIL | One listed 85-inch TV PDP temporarily landed on the 75-inch model; exact identity gate rejected it. |
| [36438033553](https://github.com/Empty-Bell/RDA/actions/runs/36438033553) | PASS | All 11 families and 557 exact SKUs; TV PDP identity 165/165; zero gate errors. |

No failed run replaced the public dashboard. The TV collector now retries an
exact-SKU failure within the same run, retaining attempt evidence. The accepted
run did not need that retry. One successful full run does not establish the
operational stability required by G6.

## Required closure work

1. **G5 history:** persist validated run snapshots by exact SKU and control;
   distinguish source changed, rule changed, failed observation and population
   change from confirmed NEW/OPEN/RESOLVED/REOPENED states. Define when a
   formerly inaccessible document may count as RESOLVED. Replay the specified
   four-run lifecycle and failed-run cases.
2. **G6 operation:** build and publish the validated dashboard artifact in a
   gated workflow; a failed integration must not race with an independent Pages
   deployment. Retain prior validated history and raw source evidence beyond
   the current 14-day Actions artifact window. Check retries, 429/timeouts,
   failure injection, resource budgets and consecutive clean full runs before
   enabling a schedule.
3. **G7 formal publication:** after G6, deploy the exact validated bundle and
   verify run/hash identity, links, filters, mobile layout and rollback. Run
   #20 is publicly served and its basic links work, but that is a narrower
   check than formal G7 acceptance.

Sources: [Run #20 unified acceptance](UNIFIED_ACCEPTANCE_RUN20.md),
[Run #19 integration record](DASHBOARD_INTEGRATION_RUN19.md), the per-model
evidence under `docs/evidence/`, and [the execution guide](EXECUTION_GUIDE.md).
