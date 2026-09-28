# RDA — Samsung US regulatory audit

Clean-room, GitHub Actions-first audit implementation targeting standard GitHub-hosted Ubuntu 24.04 x64.

## Current status

- **G0 and G1 accepted.** Source reconnaissance, runtime, schema, CLI, fixture and quality gates have acceptance records.
- **G2 formally open.** The refrigerator has a 75-SKU source and ENERGY STAR vertical slice, but full source comparison, whole-product decisions and operational acceptance remain.
- **G3 and G4 preparatory.** Later-family source collection and candidate exploration have run; neither gate is formally accepted. G5–G7 have not started.
- **Reviewed dashboard snapshot published.** The [11-family GitHub Pages dashboard](https://empty-bell.github.io/RDA/) shows 557 model-level records from separate reviewed family runs. It is a static snapshot, not a single unified audit run or formal phase acceptance. Automated cross-family refresh and the planned operational dashboard remain open.

The active checkpoint, current workflow links and remaining tasks are in [docs/CURRENT_TASK.md](docs/CURRENT_TASK.md). Phase history and acceptance boundaries are in [docs/PHASE_STATUS.md](docs/PHASE_STATUS.md); scope and evidence rules are in [docs/MASTER_PLAN.md](docs/MASTER_PLAN.md) and [docs/EXECUTION_GUIDE.md](docs/EXECUTION_GUIDE.md).

Hosted GitHub Actions runs are the execution evidence. A successful source or candidate workflow does not by itself establish a compliance PASS or close a phase gate.
