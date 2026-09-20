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
  Hosted contract run 35204222516 passed. EPA pattern `RF23D*9600**`
  positionally includes normalized `RF23DB9600QL`, hence observed exact SKU
  `RF23DB9600QLAA` under the approved terminal suffix policy. The EPA row has
  no separate additional-model list. Offline report v3 now records explicit
  model_pattern_inclusion INCLUDED/NOT_INCLUDED/UNKNOWN separately from current
  certification, US applicability and assessment. It reads the saved actual EPA
  row fixture and retains its body hash/PD_ID. Non-inclusion in this one pattern
  is not absence of certification. D09 proposal is now
  G2_D09_CURRENT_US_POLICY_PROPOSAL.md: pattern inclusion, observed US market
  and current certification remain independent. User authorized bounded
  `OBSERVED_US_MARKET`; offline report records literal US tokens with
  EPA_ROW_ONLY scope, raw markets/date and source URL/hash. Current certification
  remains NOT_EVALUATED. Current-status source research found EPA Model Index
  8wj2-sec8, explicitly described as currently certified models. Read-only PD_ID
  2839420 query matched brand/model/CB identifier; not hosted evidence yet.
  See G2_EPA_CURRENT_STATUS_RECON.md. Next: manual hosted raw/hash metadata and
  PD_ID capture with exact-key fixture validation. Hosted capture 35208691273
  and replay contract 35210140588 passed. The user approved the bounded current
  snapshot observation. Report v4 now emits
  `OBSERVED_CURRENT_CERTIFIED_INDEX` only when the saved Model Index and
  refrigerator projections agree exactly on PD_ID, brand, model pattern and CB
  identifier; it retains the Index row hash and raw certification date. Missing
  or mismatched keys remain `NOT_EVALUATED`; assessment remains disabled. The
  EPA Current Model Index is the sole EPA certification comparison source.
  G2_CURRENT_INDEX_CLAIM_COMPARISON.md documents the approved three-point rule:
  registered plus PLP logo/PDP logo/affirmative Spec certification all present
  yields PASS for this check; any confirmed missing point yields LOW consistency.
  Unregistered after complete valid search plus any positive point yields HIGH.
  Existing issue codes are reused; runtime activation waits for collection gates.
  The saved diagnostic now marks current_index_observation_scope=EPA_ROW_ONLY:
  a nonincluded SKU is not certified or uncertified by the compared row. The
  hosted Samsung-scope Current Model Index capture/replay now PASSed in run
  35224820966 at ada6ea4 on ubuntu-24.04. It preserved raw metadata, before/after
  counts and every Samsung page, then replayed each raw hash; artifact
  `g2-epa-current-index-samsung-35224820966-1` is 56,566 bytes. The scope is
  `upper(brand_name) = 'SAMSUNG'` without a guessed refrigerator filter. This
  establishes complete source-query evidence only, not an individual SKU result
  or assessment. Exact-target candidate projection is now implemented and hosted
  contract CI run 35225714504 PASSed at 1899c91. It requires same-run verified
  PDP targets, preserves every raw/approved-normalized literal candidate and
  withholds a no-match result while any EPA pattern encoding remains unresolved.
  See G2_CURRENT_INDEX_CANDIDATE_PROJECTION.md. The same-run refrigerator target
  feed and strict p5st-her9 four-key provenance bridge are now defined and hosted
  contract CI run 35226584964 PASSed at debd8e4. Only verified PDP SKUs enter the
  feed; a pattern diagnostic runs only after its Current Index and refrigerator
  rows match on PD_ID, brand, model pattern and CB identifier. This remains a
  candidate-only result. See G2_REFRIGERATOR_PATTERN_BRIDGE.md. It is now
  integrated in one bounded live refrigerator execution: hosted run 35227238209
  PASSed at f2efd97 on ubuntu-24.04 in 3m33s. The run verified PDP targets,
  captured the complete Samsung Current Model Index snapshot under the same UUID,
  replayed raw EPA evidence and wrote the target feed/candidate projection into
  the pilot artifact. Artifact `g2-pilot-35227238209-1` has GitHub digest
  `e83145ee8aaa9297db0dc4faffc656b5fe401a1cbf3f385882699dc3ee4d7021`.
  Assessment remains disabled until collection definitions and coverage are
  complete. Same-run p5st-her9 raw-row capture is now integrated for compatible
  pattern candidates only. Hosted refrigerator run 35228688716 PASSed at a639e42
  on ubuntu-24.04 in 3m33s; its `g2-pilot-35228688716-1` artifact is 3,522,140
  bytes. The run preserved p5st metadata and exact PD_ID responses, then applied
  the four-key bridge only to compatible candidates. This remains candidate-only,
  with current certification and assessment NOT_EVALUATED. Next: add the
  three independent Samsung publication-point collectors (PLP logo, PDP logo and
  visible Spec certification) with target attribution and PRESENT/ABSENT/UNKNOWN
  boundaries. Recommended model: Terra medium.

  The first implementation now records the three points separately in each live
  refrigerator pilot artifact. A PLP point accepts only an Energy Star image in
  the exact model card. A PDP point accepts only the existing exact-identity,
  primary-surface image attribution. A Spec point accepts only affirmative text
  in a visible rendered Spec row; raw `energyStarFlg` and bridge-data fields are
  never treated as a visual point. Unknown layouts remain UNKNOWN. This is a
  collection gate only: no PASS/LOW/HIGH rule is activated until the hosted run
  and real captured DOM output are reviewed. Hosted run 35229879599 PASSed on
  ubuntu-24.04 at ce5b0b7 (4m17s; artifact 10500403275; digest
  05e141a9e1f66d501f9f09f54c618fe007b892640fa665ec97913ce82c818187).
  It collected 10 exact PDPs: PDP logo PRESENT 10/10, PLP logo PRESENT 4/10
  (six exact cards not mounted, so UNKNOWN), and Spec UNKNOWN 10/10. Manual
  source review found the reason: Samsung mounts `#specs` only after pressing
  the visible `Specs` tab; its row schema is `Specs_subSpecItem__`, with the
  actual observed example `ENERGY STAR® Certified | Yes`. Next: activate that
  tab in the hosted collector and review the resulting complete visible table.
  Recommended model: Terra medium.

  User-provided PDP/PLP selector paths are now being hardened for the live
  collector: retain the stable PDP `#leftColumnInMainContent`, gallery-label
  class fragment and Energy Star image filename; retain the PLP card's
  energy-star-label wrapper but never its ordinal card position or absolute
  XPath.  Raw PF `energyStarFlg` and exact-SKU Bridge Spec rows are retained as
  separate source declarations on each publication record. They do not replace
  visual points or activate a rule. Next: verify this selector/declaration
  contract on ubuntu-24.04 and then replace broad browser collection with
  direct-source collection plus bounded template checks. Recommended model:
  Terra medium.

  The approved collection boundary has since changed: Energy Star checks use
  Samsung source declarations rather than visual selector evidence.  The live
  G2 Energy Star source run captures, for every current exact PF SKU, its own
  PF `energyStarFlg`, its own PDP Next `energyStarFlag`, and its own Bridge
  ENERGY STAR Spec rows.  A representative SKU value is never shared with a
  variant.  Samsung requires a headless session to return PF/Bridge JSON, but
  the collector performs no selector, image, or visible-UI inspection; Next
  and EPA calls are ordinary source requests.  Hosted run 35239931659 passed
  on ubuntu-24.04 at d9c3ee6 in 4m00s. Artifact
  `g2-energy-star-source-35239931659-1` is 6.82 MB with digest
  `dbd2a8c6e7f06dbebfc0c75f189630eda1e38088534543ca08d5f84a8f1d9442`.
  The output is source collection only: EPA comparison and PASS/LOW/HIGH rule
  activation remain disabled. Next: bind the same-run Current Model Index to
  these exact-SKU declarations, then review the three-point rule inputs.
  Initial PF-to-rendered-PLP calibration at 4a89246 used the page-wide
  `.pd21-product-card` container and was invalid: it associated badges from
  other cards. It produced four false positive logo observations. The collector
  now scopes a card to the immediate child of the product list, requires its
  distinct `data-modelcode` set to contain only the inspected exact SKU, and
  fails when another SKU is present. Repeated anchors for that same SKU are
  normal Samsung card markup and are retained as raw occurrence counts. Hosted
  ubuntu-24.04 rerun 35409051794 at 09a502c PASSed; artifact
  `g2-pf-plp-visual-validation-35409051794-1` has ZIP SHA-256
  `ab20111229d12523c30352fc69bc1f4919db43950774b994f0847a46635a847e`.
  It observed 75 current PF exact SKUs and all 41 rendered exact PLP cards:
  37 PF `Y`/logo-present and 4 PF `N`/logo-absent, with zero disagreement.
  The other 34 exact SKUs were not rendered cards and were not judged absent.
  This validates PF `energyStarFlg` as the per-exact-SKU PLP source declaration
  for the currently observable representative-card sample, including both
  values. It does not visually validate unrendered variants, which continue to
  use only their own PF raw value and never inherit a representative result.
  Same-run Current Model Index binding is now complete. Hosted ubuntu-24.04
  run 35409373091 at f7a28b8 PASSed in 4m43s; artifact
  `g2-energy-star-source-35409373091-1` has ZIP SHA-256
  `c4c65092dda7b17f284ddf0b5cb6487fc8479ee0287f28e75500ac51d9d01d51`.
  All 75 per-SKU PF/PDP Next/Bridge declarations were bound to the same UUID
  Current Model Index capture. Each has `UNRESOLVED_PATTERN_ENCODINGS_PRESENT`:
  the Index exposes wildcard model patterns, so none is current-certified or
  uncertified by this step. All 75 records retain
  `current_certification_state=NOT_EVALUATED` and `assessment=NOT_EVALUATED`.
  The three-point source input review is now complete. Hosted ubuntu-24.04 run
  35410182480 at e5a61fa PASSed in 4m08s; artifact
  `g2-energy-star-source-35410182480-1` has ZIP SHA-256
  `429c2e3960a5bb8b4e1c797bdc852505fbb40941cfcc06b68ae873eb80a2230b`.
  It has one non-assessing record per 75 exact SKU: PF PLP and PDP Next flags
  agree as `Y/Y` for 68 and `N/N` for 7; Bridge Spec rows and same-run EPA
  candidate references are retained alongside them. All 75 EPA candidates
  still contain wildcard encodings, so certification and assessment stay
  `NOT_EVALUATED`. The input-review transformation itself is offline; Samsung
  PF/Bridge session transport remains the collection-time bottleneck. The
  bounded positional diagnostic is now applied to the same-run pattern
  candidates. Hosted ubuntu-24.04 run 35543232715 at 219981a PASSed; artifact
  `g2-energy-star-source-35543232715-1` has ZIP SHA-256
  `a1315ec33a4026823ae88921590b2c3a19dd7ac04c56c2db538fb7103b683a12`.
  It retained all 75 exact SKUs, found 49 normalized-SKU/pattern pairs that
  were positionally compatible, and retained 44 only after p5st reproduced
  the Current Index row with the same PD_ID, brand, model pattern and CB
  identifier. Five checks were withheld because their p5st PD_ID response was
  not exactly one row: RF90F23AECEAA, RF90F23AECRAA (3943242), RF90F29AECEAA,
  RF90F29AECRAA (3943244), and RZ11M7074SA/AA (2362230). A withheld check is
  not a finding that the model lacks EPA registration. Every record still has
  `current_certification_state=NOT_EVALUATED` and `assessment=NOT_EVALUATED`.
  Next: reduce the Samsung PF/Bridge session-transport collection bottleneck
  without changing the per-exact-SKU source declaration boundary.
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
