# RDA — Samsung US regulatory audit

Clean-room, GitHub Actions-first audit implementation targeting standard GitHub-hosted Ubuntu 24.04 x64.

## Current status

- **G0 and G1 accepted.** Source reconnaissance, runtime, schema, CLI, fixture and quality gates have acceptance records.
- **G2 accepted for its recorded refrigerator controls.** The 75-SKU source was reassessed under the current missing-Specs-field rule; whole-product legal compliance remains unevaluated.
- **G3 and G4 bounded control execution accepted.** [Unified hosted run 36438033553](https://github.com/Empty-Bell/RDA/actions/runs/36438033553) freshly collected and assessed all 11 families under one source run. Its gate passed with 557 exact models and no integrity errors. See [Run #20 acceptance record](docs/UNIFIED_ACCEPTANCE_RUN20.md).
- **Integrated dashboard Run #20.** The [GitHub Pages dashboard](https://empty-bell.github.io/RDA/) has the source-bound 557-model snapshot (485 PASS / 23 HIGH / 11 MEDIUM / 38 LOW), model evidence and CSV/Excel exports. Whole-product legal compliance remains unevaluated. G5–G7 operational acceptance is still separate.

The active checkpoint, current workflow links and remaining tasks are in [docs/CURRENT_TASK.md](docs/CURRENT_TASK.md). Phase history and acceptance boundaries are in [docs/PHASE_STATUS.md](docs/PHASE_STATUS.md); scope and evidence rules are in [docs/MASTER_PLAN.md](docs/MASTER_PLAN.md) and [docs/EXECUTION_GUIDE.md](docs/EXECUTION_GUIDE.md).

Hosted GitHub Actions runs are the execution evidence. A successful source or candidate workflow does not by itself establish a compliance PASS or close a phase gate.
