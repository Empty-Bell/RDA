# Working contract

1. Read relevant docs/contracts before editing; read MASTER_PLAN on first entry.
2. Never infer undocumented audit semantics; record real ambiguity in DECISIONS.
3. Ask the user only when a real semantic decision is required.
4. Do not change rules merely to pass tests.
5. Keep audit semantics separate from dashboard changes.
6. No destructive git reset/clean.
7. Clean-room implementation; no proprietary source copying.
8. Never hardcode current population counts or run numbers.
9. No new issue code without approval.
10. Pipeline error never becomes PASS.
11. Preserve raw evidence before interpretation/correction.
12. External parsers require sanitized fixtures and contract tests.
13. Every compliance rule requires unit tests.
14. Every phase ends PASS/FAIL/BLOCKED, backed by hosted Actions evidence.

Current formal gate: Phase 2 refrigerator audit remains open. G0 and G1 are
accepted; see docs/G0_ACCEPTANCE_RECORD.md and docs/G1_ACCEPTANCE_RECORD.md.
The user has also authorized preparatory source work for downstream families;
this does not accept G3/G4 or enable unapproved assessment rules. Clothes Dryer
is EPA ENERGY STAR-focused only. Do not collect/retrieve/OCR EnergyGuide PDFs or
run PDP/label/EPA numeric comparisons for Dryer. See MASTER_PLAN §1.1 and
DRYER_SOURCE_CONTRACT.md.
Only approved assessment rules may run; check DECISIONS.md and the family contract.
Unapproved semantic policies remain disabled; draft contracts do not resolve decisions.
No unapproved compliance decision engine or Pages deployment.
Use standard ubuntu-24.04 x64. Local success does not pass hosted gates.
Token economy: inspect relevant fields/diffs only; no agents; no LLM in audit runtime.

For next-step continuation, read docs/CURRENT_TASK.md first and only relevant
changed contract/code sections; avoid repeatedly reading full chronological docs.
