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
- Checks: checks/g1/test_normalization.py, CI workflow ci.yml. Normalization helper
  is not yet wired into live pilot facts. The pilot still preserves raw observations.
- Next: wire normalized source observations with same-run raw/evidence references;
  verify from saved source fixtures first. Expand PDP collection only after that.
  Do not infer claim/certification validity or OCR correction from normalization.
- No agents, LLM runtime, schedule or publication. Standard ubuntu-24.04 x64.
- Token economy: default Terra medium for bounded implementation; Luna low for
  simple docs/fixture edits; Sol medium only for unresolved OCR/rule-boundary review.
  This is a recommendation, not an automatic model-setting change.
- Separate cheap offline schema/normalization CI from expensive live collectors.
  Never rerun live collectors for docs-only or pure normalization changes.

Repository root: C:/Users/JB/Documents/Coding/RDA/repo.
Local Python: runtime/g1-venv/Scripts/python.exe (ignored dev venv).
Local test env PYTHONPATH=src (add scripts for checks/g2).
Hosted G1 CI installs requirements-g1-tools.lock, runs quality.py plus run.py.
Use git safe.directory override. Git write/network may need sandbox escalation.
