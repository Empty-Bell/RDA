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
- Label field contract adopted for conservative fixture selection; annual-energy
  selection is now live only for reviewed byte-identical records. Capacity/model
  selection and identity/correction policies are not enabled.
- Fixture selector checkpoint: run 35177064002 at 8e03ee7 passed 14 contracts on
  hosted Python 3.11/3.12. It selects only the unique 700 kWh refrigerator fixture
  candidate and leaves multiplicity, disagreement and provenance mismatch unobserved.
  This historical fixture checkpoint was followed by the live binding below.
- Expanded corpus review/replay is complete. Nine saved extra labels were bound to
  PDF/page/detection annotations; eight select only under that contract and
  RF22A4111 stays unobserved because 109 and 585 occur as raw candidates. Live
  integration checkpoint 35179885437 at 1cd83df PASSed on ubuntu-24.04: a value is
  recorded only when the newly collected exact-SKU PDF hash and reviewed detection
  IDs match. Assessment, comparison and EPA matching remain disabled. See
  G2_CORPUS_REVIEW.md and g2-label-corpus-replay.json.
- Live observation-summary checkpoint: run 35180415335 at 4f505fb PASSed on
  ubuntu-24.04. The checkpoint now exposes one review-bound result per collected
  label document (SKU, document index, PDF hash, observation state and reason) and
  `VALUE`/`NOT_OBSERVED` counts without producing an assessment. Artifact 10479947693
  ZIP digest: 79e5514b656a16529b149974ffa77d1318ea386eb3b830a3eceb7a6f7b0fd4ec.
- Capacity/model boundary review: G2_CAPACITY_MODEL_REVIEW.md and the sanitized
  g2-capacity-model-review.json preserve five distinct PDF descriptor/box reviews.
  All nine SKU projections were checked against saved original PDF bytes and raw
  detection text/boxes. RF18A5101 loses visible stars; RF22A4111 substitutes a
  quotation mark despite high OCR confidence. Keep raw OCR and visual annotation
  separate; no model correction, glob/prefix matching or capacity identity rule.
  Hosted cheap contract run 35181212977 at 4ba3dd6 PASSed 25 cases on Python
  3.11/3.12; no live collector was rerun.
  Next: fixture-only capacity selection with explicit descriptor/unit and reviewed
  detection binding; live capacity remains disabled. The capacity selector and
  nine-SKU saved-corpus replay PASSed; hosted run 35181720506 at 23ba5a1 passed
  27 contracts on Python 3.11/3.12. Next: bind it to fresh live bytes only.
  Live binding checkpoint 35181903264 at 55a7e20 PASSed on ubuntu-24.04. Fresh
  bytes must match the saved capacity review; checkpoint records its own capacity
  observation summary. No identity/comparison/assessment policy changed. Next:
  expose the joined annual/capacity source observations in the report. This is now
  complete: report rows retain document URL/hash/status, each reviewed source
  measurement and evidence IDs without deriving an assessment. Hosted G1 fixture
  CI 35182804474 and G2 contract CI 35182804467 PASSed at 19bf045. Next: bounded
  report replay against the saved live artifact. This now PASSed: G2 hosted run
  35183198414 at 28b62b1 rebuilt and compared every report entry against the
  same-run bundle; artifact 10481426384 ZIP digest is
  2af6aa68bf3e79d0bf1f1364eff835f03ca9d312e323bdaa69293c2427121677.
  Next: model descriptor source-observation projection only. Recommended model:
  Luna low. This is now complete: `label_model_raw` is copied only from a unique
  raw field-candidate token with its original evidence references; ambiguity stays
  NOT_OBSERVED and wildcard correction/SKU matching remain disabled. Hosted G1 CI
  35184128574, G2 contract CI 35184128573, and live ubuntu-24.04 run 35184128593
  PASSed at 8d86408. Artifact 10481173998 ZIP digest:
  096e7a6a99d0c7c629410dd5506f2fc282e338c309db6fe0c454ebf4650dd8a9. See
  G2_MODEL_SOURCE_OBSERVATIONS.md. Next: draft an explicit wildcard correction and
  identity-matching policy for human review only; no implementation or matching.
  Recommended model: Sol medium. The user approved the bounded fixture-only evidence
  contract, and hosted G2 run 35188432065 PASSed at 6588115 on Python 3.11/3.12
  (34 tests). It validates review provenance and withholding of wildcard/suffix/
  OCR-confusion cases; no live crawl occurred. Next: independent source-backed
  wildcard grammar and EPA identity evidence reconnaissance proposal, without
  matching implementation. Recommended model: Sol medium. This research is now
  documented in G2_EPA_WILDCARD_RECON.md: EPA single-position guidance was found,
  but character-class and Samsung label/suffix scope remain unresolved. Next:
  bounded hosted source capture/replay of official guidance, metadata and one EPA
  record; no matcher. This is now PASSed: hosted run 35189522017 at ae632c7
  captured five official sources and replayed their raw SHA-256 evidence. Artifact
  10483337728 ZIP digest: 6293ab90b6ac297e3bc457477476ddb4ce0b8abb7774ae34cc1ed60678859926.
  Next: review captured dataset-scoped grammar and draft a proposed matching matrix;
  no matcher. Recommended model: Sol medium. Review found the Product Finder
  HTML was only a JS shell. Follow-up ef0da55 adds literal PD_ID API capture and
  raw/projection replay; hosted run 35189830486 PASSed (5 source-contract tests).
  Artifact 10483857141 ZIP SHA256:
  8a799f87f8f9e0d1698e37c559f810ba4b810bc93f2eb1f37473601131cb1fd2.
  G2_EPA_MATCHING_MATRIX_PROPOSAL.md records reviewed scope; grammar remains draft.
  Small actual-source projection fixture and tampering contracts are now PASSed in
  hosted run 35190205775 at b283074 (6 tests). Artifact 10483347557 ZIP SHA256:
  2fd920e4c8419fa1a90d7abfb0bb98bfb576b5410bac3a44aa72cac55d748aca. Next:
  decide whether to approve a dataset-scoped positional diagnostic; no automatic
  matcher or assessment. Recommended model: Sol medium.
  The user approved the concrete offline positional diagnostic request in
  G2_EPA_MATCHING_MATRIX_PROPOSAL.md:
  offline p5st-her9 positional diagnostic only, uppercase A–Z star slots and
  digit hash slots, full-length equality, immutable raw values and unchanged
  identity/correction states. Implementation is complete: hosted run 35191030514
  PASSed at 6c43029 with 7 tests; artifact 10483914100 ZIP SHA256:
  23f308a90d76685e5206539a7f2fe65f568645394dbacb1464fc57c3125f259d. Next:
  review diagnostic outputs against the refrigerator corpus; no live matching or
  assessment. This is now PASSed: hosted run 35195946960 applied the diagnostic
  to 9 saved SKU observations. Artifact 10486160033 ZIP SHA256:
  8b766e3c94b2e7bc557be6323fdfe52b877a0e6fc55ac7aa387d0c256ebfa20c. All raw
  strings remain preserved and identity/correction states remain disabled. Corpus
  review is recorded in G2_EPA_DIAGNOSTIC_CORPUS_REVIEW.md: five records were
  withheld for `/AA` syntax and four for length; none became compatible. Keep v1
  unchanged. Official suffix research is recorded in
  G2_SAMSUNG_SUFFIX_SOURCE_REVIEW.md: Samsung US displays
  `RF23DB9600QL / RF23DB9600QLAA` together, but no general suffix deletion or
  EPA identity rule was established. Hosted run 35202527763 captured the
  source-declared pair and replayed its raw hash successfully; see
  G2_SAMSUNG_SUFFIX_SOURCE_REVIEW.md. Next: retain it as one observational
  pair and investigate explicit EPA additional-model mappings. User approved
  terminal Samsung `AA`/`/AA` removal only: preserve raw exact SKU and every
  preceding character; this remains identity/assessment NOT_EVALUATED. Next:
  apply that bounded observation to the offline positional diagnostic report.
  Hosted contract run 35204222516 passed. EPA PD_ID 2839420 still has no
  additional-model field, so no explicit mapping exists for the Samsung pair.
  Next: define the D09 evidence threshold for identity/current/US separately;
  recommended model Sol medium.
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
