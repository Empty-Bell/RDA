# RDA — Samsung US regulatory audit

Clean-room, GitHub Actions-first audit implementation targeting standard GitHub-hosted Ubuntu 24.04 x64.

## Current status

- **G0 and G1 accepted.** Source reconnaissance, runtime, schema, CLI, fixture and quality gates have acceptance records.
- **G2 accepted for its recorded refrigerator controls.** The 75-SKU source was reassessed under the current missing-Specs-field rule; whole-product legal compliance remains unevaluated.
- **G3 family controls accepted; G3 overall open.** All 11 families have hosted, source-bound assessment artifacts. Their source collections occurred in different runs, so one unified source execution remains outstanding. G4–G7 have not been formally accepted.
- **Integrated dashboard Run #19 published.** The [GitHub Pages dashboard](https://empty-bell.github.io/RDA/) reconciles 557 exact models (479 PASS / 29 HIGH / 11 MEDIUM / 38 LOW) to all 11 accepted family artifacts and provides model evidence and CSV/Excel exports. The hosted integration gate passed; the mixed-source snapshot is not a single audit source run or whole-product compliance verdict.

The active checkpoint, current workflow links and remaining tasks are in [docs/CURRENT_TASK.md](docs/CURRENT_TASK.md). Phase history and acceptance boundaries are in [docs/PHASE_STATUS.md](docs/PHASE_STATUS.md); scope and evidence rules are in [docs/MASTER_PLAN.md](docs/MASTER_PLAN.md) and [docs/EXECUTION_GUIDE.md](docs/EXECUTION_GUIDE.md).

Hosted GitHub Actions runs are the execution evidence. A successful source or candidate workflow does not by itself establish a compliance PASS or close a phase gate.
