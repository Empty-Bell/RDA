# Compact continuation context

Read AGENTS.md and this file first; inspect only the relevant implementation and
contract sections. Do not reread chronological phase history or full source files
on every next-step prompt. Same-task model changes should continue existing work.

- G0 and G1 accepted PASS; G2 RUNNING, no G2a–e gate accepted.
- User approved exact-SKU identity, independent findings/unique affected SKU counts,
  fresh UUID execution IDs and no overwrite. No reapproval needed.
- Open G2 policies: energy/test basis/tolerance, OCR corroboration/correction,
  current/US/wildcard certification identity, priority/summary and error boundaries.
- Current live pilot: scripts/g2_smoke.py / g2_population.py / g2_pdp.py.
- Hosted last source checkpoint 35173796328 at 21b621a: 75 population SKUs,
  5 verified PDP identities, 0 failed, 70 unattempted; one original label;
  EPA brand snapshot context only. 30 tests; evidence 105 verified. Partial,
  NOT_EVALUATED. See docs/evidence/g2-pdp-coverage-recon.json.
- New source normalization: src/regaudit/normalization.py. Explicit kWh/yr/year
  and source-declared cu ft; three independent claim channels; raw/reason retained.
  Unknown/ambiguous/conflicting encodings do not become false or findings.
- Normalization checkpoint 35174268354 / 55f2f4a: Python 3.11/3.12 each passed
  94 fixtures + 15 quality checks, zero skipped. Evidence: g2-normalization-recon.json.
- Normalization integration checkpoint: compact fixture gate 35174728382 at
  6ac294d passed six adapter cases on hosted Python 3.11/3.12. Live pilot run
  35174846442 at bd19bfd passed on ubuntu-24.04, retaining five normalized PDP
  source channels with same-run bridge/raw/derived evidence references. See
  docs/evidence/g2-normalization-integration-recon.json.
- PDP coverage expansion checkpoint: run 35175307189 at d884b4c passed on hosted
  ubuntu-24.04 with a deterministic maximum of ten PDP attempts. A selected
  identity failure would fail the workflow; this result does not mean complete
  population, label or EPA coverage. See
  docs/evidence/g2-pdp-coverage-expansion-recon.json.
- EnergyGuide document planning checkpoint: run 35175865085 at ed1d994 passed
  ten offline contracts on hosted Python 3.11/3.12. Each verified PDP retains all
  exact-SKU Support-declared HTTPS document candidates; no canonical PDF is chosen.
- Expanded EnergyGuide observation checkpoint: run 35176346751 at ddad8ff passed
  on hosted ubuntu-24.04. Extra bounded PDP labels retain original PDF bytes,
  extraction observations and unselected field/layout candidates; multiple Support
  PDFs remain evidence-only. No canonical value, OCR correction or assessment exists.
- Label selection proposal: docs/G2_LABEL_SELECTION_PROPOSAL.md is REVIEW_REQUIRED.
  Reviewed committed refrigerator text/layout corpus; expanded artifact individual
  files still require replay/review. No selector is enabled. Obtain approval for the
  proposed extraction contract before implementing canonical field selection.
- No agents, LLM runtime, schedule or publication. Standard ubuntu-24.04 x64.
- Token economy: default Terra medium for bounded source integration/collection;
  Luna low for docs, fixture-only tests and workflow maintenance; Sol medium only
  for unresolved OCR/rule-boundary review.
  This is a recommendation, not an automatic model-setting change.
- Separate cheap offline schema/normalization CI from expensive live collectors.
  Never rerun live collectors for docs-only or pure normalization changes.

Repository root: C:/Users/JB/Documents/Coding/RDA/repo.
Local Python: runtime/g1-venv/Scripts/python.exe (ignored dev venv).
Local test env PYTHONPATH=src (add scripts for checks/g2).
Hosted G1 CI installs requirements-g1-tools.lock, runs quality.py plus run.py.
Use git safe.directory override. Git write/network may need sandbox escalation.
