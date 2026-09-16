# RDA — Samsung US regulatory audit

Clean-room, GitHub Actions-first implementation. Target: standard GitHub-hosted Ubuntu 24.04 x64.

Current scope: **Phase 0 runtime/source reconnaissance**, no compliance rules or public dashboard.

The initial push runs `runner-probe.yml`; subsequent manual runs are available in Actions.
It installs dependencies without cache, tests embedded-text PDF and image-only OCR,
launches headless Chromium, observes refrigerator PLP network traffic, and probes the official ENERGY STAR catalog.
Failure diagnostics are uploaded as `phase0-probe-<run_id>-<attempt>` (14 days).

Runtime checks use synthetic labels, explicitly distinct from captured public-source fixtures.
Probe success is not full Phase 0 acceptance: pagination, exact SKU identity, EnergyGuide provenance,
11-family EPA adapters, hosted live PDF extraction, and source contract tests still require verification.

See docs/MASTER_PLAN.md, docs/EXECUTION_GUIDE.md, and docs/PHASE_STATUS.md.
