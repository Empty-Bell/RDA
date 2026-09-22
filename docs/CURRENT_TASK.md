# Compact continuation context

## Latest G3 checkpoint — Clothes Dryer evidence collection (2026-09-22)

The TV audit uses model identity only. Dryer source reconnaissance passed on
hosted Ubuntu in run 35712517039. Exact-SKU PDP collection passed in run
35712660255: all 54/54 products have verified exact PDP identity, with zero
failed or unattempted SKUs. The artifact retains PDP Specs/Support, claim channels,
EnergyGuide links and provenance; it does not EPA-match or assess. Combo washer
Energy Guide kWh is not projected as dryer annual energy. A later duplicate
collection attempt (35713169010) failed at its upstream source-artifact identity
guard before PDP collection; use the complete, successful 35712660255 package.
The next step is parallel same-run capture of EPA Current Samsung dryer rows and
PDP-declared EnergyGuide PDFs. Comparison and assessment remain disabled pending
review of fuel, venting and combo applicability. Ten existing Dryer contract tests
and the full 184-test suite pass locally (one skipped). Recommended model for
fixed-schema capture review: GPT-5.6 Luna low; use GPT-5.6 Terra medium only if
source evidence requires a new policy decision. Actions runtime uses no LLM.

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
  The former p5st pattern diagnostic and its evidence were retired by explicit
  instruction. The EPA Current Model Index is the only EPA comparison source.
  Official suffix research is recorded in
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
  See G2_CURRENT_INDEX_CANDIDATE_PROJECTION.md. The former p5st cross-dataset
  bridge was removed from code, workflows and task evidence because it is not
  part of the Current Index-only comparison. Next: add the
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
  Current Model Index capture. The first binding kept wildcard rows unresolved;
  the Energy Star binder now compares those patterns directly against the
  normalized exact SKU under the approved fixed-position rule. This determines
  only same-run Current Index pattern candidates; assessment remains separate.
  All records retain `current_certification_state=NOT_EVALUATED` and
  `assessment=NOT_EVALUATED` pending the final rule-activation gate.
  The three-point source input review is now complete. Hosted ubuntu-24.04 run
  35410182480 at e5a61fa PASSed in 4m08s; artifact
  `g2-energy-star-source-35410182480-1` has ZIP SHA-256
  `429c2e3960a5bb8b4e1c797bdc852505fbb40941cfcc06b68ae873eb80a2230b`.
  It has one non-assessing record per 75 exact SKU: PF PLP and PDP Next flags
  agree as `Y/Y` for 68 and `N/N` for 7; Bridge Spec rows and same-run EPA
  candidate references are retained alongside them. All 75 EPA candidates
  still contain wildcard encodings, so certification and assessment stay
  `NOT_EVALUATED`. The input-review transformation itself is offline; Samsung
  PF/Bridge session transport remains the collection-time bottleneck. EPA
  comparison uses only the same-run Current Model Index binding; p5st capture,
  cross-dataset bridges and their prior evidence are removed. Next: reduce the
  Samsung PF/Bridge session-transport collection bottleneck
  without changing the per-exact-SKU source declaration boundary.
  The five former p5st holds have all been resolved directly against the
  preserved Current Index page rows from successful run 35544478856 (artifact
  SHA-256 `eb9da55d442ae29bf8721b829e23263cd359254afbaa17ef5d3eb613fa35047b`).
  RF90F23AECEAA and RF90F23AECRAA match `RF90F23AE**` (PD_ID 3943242);
  RF90F29AECEAA and RF90F29AECRAA match `RF90F29AE**` (PD_ID 3943244); and
  RZ11M7074SA/AA normalizes to `RZ11M7074SA`, matching `RZ11M7074**`
  (PD_ID 2362230). The binder now records these as
  `MATCHED_CURRENT_INDEX_POSITIONAL_PATTERN_CANDIDATES` without requesting
  p5st. Hosted run 35545792333 passed on ubuntu-24.04 at 9dc064a; artifact
  `g2-energy-star-source-35545792333-1` has ZIP SHA-256
  `9e56598235c01cb25b4fc3cf916607e7fde29c1b81d01bbfe46448c284cc3489`.
  The artifact confirms exactly one Current Index pattern candidate per SKU,
  sourced from page-0006 for the RF90F rows and page-0001 for RZ11M7074SA/AA.
  All five have zero unsupported patterns; certification and assessment remain
  `NOT_EVALUATED` until the final policy activation step.
- Final refrigerator Energy Star assessment is active. Hosted ubuntu-24.04
  run 35547213219 at `50ca9cc` passed; artifact
  `g2-energy-star-source-35547213219-1`, ID 10617170631, ZIP SHA-256
  `93084dfa227992b883d86faee4fcd15f943051f9c6dfc36090011dcdb31c8072`.
  Complete same-run evidence covers 75/75 exact SKUs, with zero missing source
  references or NOT_EVALUATED records. The initial `*` wildcard matcher was
  corrected because EPA rows use it for alphanumeric positions, not letters
  only. Hosted rerun 35548351322 passed at `3d0e571`; corrected results are
  52 PASS, 4 LOW consistency findings, 14 HIGH eligibility findings and 5
  NO_FINDING. This completes the
  refrigerator ENERGY STAR publication check only; it is not whole-product
  compliance PASS and does not complete the remaining G2 or later phases.
- No agents, LLM runtime, schedule or publication. Standard ubuntu-24.04 x64.
- Token economy: default Terra medium for bounded source integration/collection;
  Luna low for docs, fixture-only tests and workflow maintenance; Sol medium only
  for unresolved OCR/rule-boundary review.
  This is a recommendation, not an automatic model-setting change.
- Separate cheap offline schema/normalization CI from expensive live collectors.
  Never rerun live collectors for docs-only or pure normalization changes.
- Energy Star review rendering is separated from source collection. The review
  workflow downloads the selected successful run's existing artifact and emits
  `energy-star-review.md`; it also runs after source workflow success. Renderer
  or review-only changes no longer trigger Samsung/EPA collection. The manual
  review workflow accepts an optional source run ID and otherwise selects the
  latest successful source run.
- Same-run Energy Star integration commit `d5aa746` passed hosted G2 run
  [35554057794](https://github.com/Empty-Bell/RDA/actions/runs/35554057794) on
  ubuntu-24.04. The single artifact has canonical report run UUID equal to the
  assessment source UUID, GitHub run ID `35554057794`, and commit
  `d5aa7469c52c6e8cfc24a819978a8d5f7c3c410b`. The canonical population and
  Energy Star assessment both cover the same 75/75 exact refrigerator SKUs;
  the assessment hash in the report matches the archived file. Corrected
  Energy Star outcomes are 57 UI PASS (52 rule PASS + 5 NO_FINDING), 4 LOW,
  14 HIGH, and 0 NOT_EVALUATED. Canonical overall product compliance remains
  NOT_EVALUATED and its assessment engine remains disabled. Artifact:
  `g2-pilot-35554057794-1`, ID `10618983718`.
- Next G2a work: expand the canonical PDP/SKU identity collection from 10/75 to
  all 75 exact refrigerator SKUs, then verify full identity coverage and
  resource/time limits on hosted Ubuntu before treating the population-to-PDP
  stage as complete. The latest run observed 10 verified, 0 failed, 65 not
  attempted. EnergyGuide/PDF/OCR coverage and the remaining G2 gates follow.
- G2a full collection is now configured: all current exact refrigerator SKUs are
  selected, `NOT_ATTEMPTED` is a hard failure, and the hosted job has a 45-minute
  cap. A successful full run is required before recording PDP identity coverage
  as complete; its accompanying EnergyGuide observations remain source evidence
  until the separate label/OCR decision gates are accepted.
- G2a full hosted run
  [35555806408](https://github.com/Empty-Bell/RDA/actions/runs/35555806408)
  passed at commit `c0e46ca`: 75/75 exact SKUs verified, 0 failed and 0
  unattempted. Artifact `g2-pilot-35555806408-1` (ID `10620777089`) contains
  75 parsed EnergyGuide facts and is about 51 MB. This completes canonical
  refrigerator population-to-PDP identity coverage; it does not complete G2b.
- G2b data-quality profile: 75 parsed EnergyGuide facts map to 58 byte-distinct
  PDFs; 71 SKUs require RapidOCR and 4 use embedded text. Current byte-bound
  review coverage yields annual energy VALUE for 8 SKUs across 4 PDF hashes and
  capacity VALUE for 9 SKUs across 5 hashes. The remaining 67/66 values stay
  NOT_OBSERVED. Raw model is VALUE for 69 SKUs; six RF90F SKUs share two PDFs
  that contain two model-pattern candidates each, so identity remains withheld.
  `scripts/g2_label_quality_report.py` and the executed notebook
  `notebooks/g2_energyguide_quality.ipynb` reproduce this profile. The offline
  quality-review workflow reads an existing successful G2 artifact and does not
  recollect Samsung/EPA sources.
- Next G2b work: generate a PDF-hash review queue for the remaining 54 annual-
  energy and 53 capacity hashes, preserving exact-SKU membership. Review and
  approve one byte-distinct PDF/panel once, then bind only explicitly covered
  exact SKUs. Do not infer model identity for the two RF90F ambiguous hashes.
- The PDF-hash review queue is now generated in both JSON and Markdown by the
  offline quality workflow. It contains 54 byte-distinct PDFs: 51 need annual
  energy and capacity review, one needs annual-energy review only, and two RF90F
  hashes are prioritized as MODEL_AMBIGUOUS because each contains two raw model
  patterns. Candidate strings and artifact entry paths are preserved per hash.
  Next: render/review each queued PDF panel, starting with the two ambiguous
  hashes and then the 51 dual-field rows; emit byte-bound annotations rather
  than changing parser output.
- The source-only Energy Star workflow is manual to avoid duplicating its full
  collection on every code push; the combined G2 pilot owns same-run reporting.
- The first two EnergyGuide review-queue PDFs were visually checked from the
  preserved full-run artifact. RF90F23 explicitly shows model patterns
  `RF90F23AE*` and `RF90F23AE**`, 618 kWh/year and 22.5 cu ft. RF90F29
  explicitly shows `RF90F29AE*` and `RF90F29AE**`, 663 kWh/year and 28.6 cu
  ft. Annual energy and capacity are now byte-hash-bound for the six affected
  exact SKUs. The two model patterns remain separately preserved and model
  identity is still NOT_EVALUATED.
- Current annotations can now be replayed offline against an existing G2 ZIP.
  The replay indexes candidate and layout files by PDF SHA-256, so an exact SKU
  can reuse a byte-identical label even when the artifact stores that raw file
  under another SKU folder. Replaying artifact 10620777089 raises reviewed
  annual-energy coverage from 8 to 14 SKUs (4 to 6 PDF hashes) and capacity
  coverage from 9 to 15 SKUs (5 to 7 PDF hashes), without Samsung/EPA access.
  The remaining queue is 52 annual-energy hashes and 51 capacity hashes; the
  two RF90F hashes stay visible as model-ambiguous even though their numeric
  fields are reviewed. Next: review the ordinary queue one PDF hash at a time,
  starting with dual-field rows, and replay each annotation batch offline.
- Hosted ubuntu-24.04 offline replay run
  [35560556408](https://github.com/Empty-Bell/RDA/actions/runs/35560556408)
  passed at `4d0a445` in under one minute. Artifact
  `g2-label-quality-35560556408-1` (ID 10622425668) contains the replayed
  selection summary and refreshed quality profile. This validates that future
  label-review batches can update coverage on a GitHub-hosted runner without
  recollecting Samsung or EPA sources.
- EnergyGuide visual-review batches 01 and 02 covered 20 additional unique PDF
  hashes and 25 exact SKUs from the preserved artifact. Offline replay now
  selects annual energy for 39/75 SKUs across 26/58 PDF hashes and capacity for
  37/75 SKUs across 26/58 hashes. The open queue fell from 54 to 35 hashes: 31
  need both numeric fields, one needs annual energy only, one needs capacity
  only, and the two RF90F hashes retain their explicit two-pattern model
  ambiguity. RF29BB8600** visibly says `Capacity: 28.8 Cubic Feet`, while its
  preserved OCR says `Gubic`; annual energy is bound but capacity remains
  NOT_OBSERVED because the selector does not silently repair OCR text. Next:
  continue batched visual review, then make a separate explicit decision on
  visually confirmed capacity OCR substitutions.
- The manual EnergyGuide PDF pass is now closed as a one-time rule-validation
  exercise. The adopted annual-energy rule selects the single explicit kWh
  candidate matching the sole annual-caption geometry proposal; unrelated cost
  numbers no longer create false ambiguity. The adopted capacity rule selects
  one exact `Capacity: <number> Cubic Feet` descriptor. A hash-bound reviewed
  exception preserves the observed `Gubic Feet` OCR text while projecting its
  visually confirmed `Cubic Feet` unit; this is not a general OCR correction.
  Offline replay selects annual energy and capacity for all 75/75 exact SKUs and
  all 58/58 byte-distinct PDFs. The numeric review queue is empty. Only the two
  RF90F multi-pattern model-identity rows remain, and their numeric fields are
  complete. Overall product compliance remains NOT_EVALUATED until PDP/label
  comparison rules run. Next: hosted-validate this source-selection contract,
  then define the EnergyGuide PDP comparison and finding rules.
- Hosted ubuntu-24.04 offline replay run
  [35562382237](https://github.com/Empty-Bell/RDA/actions/runs/35562382237)
  passed at `cf43651`. Artifact `g2-label-quality-35562382237-1` (ID
  10622577282) confirms 75/75 annual-energy values and 75/75 capacity values
  across all 58 PDF hashes under the automatic source-selection contract. The
  numeric exception queue is empty; only the two already documented RF90F
  multi-pattern model observations remain outside numeric selection.
- A non-assessing PDP/EnergyGuide numeric comparison now covers all 75 exact
  SKUs. Annual energy is comparable for 51 SKUs and all 51 are exactly equal;
  24 have no PDP annual-energy observation. Capacity is comparable for 69 SKUs:
  62 are equal and seven differ by 0.3–0.5 cu ft; six have no PDP capacity.
  `scripts/g2_energyguide_numeric_comparison.py` records EQUAL, DIFFERENT and
  NOT_COMPARABLE without tolerance, severity or findings. The recommended V1
  finding policy is documented in G2_ENERGYGUIDE_NUMERIC_COMPARISON_PROPOSAL.md
  and remains disabled pending explicit approval of its new issue code/severity.
- EPA refrigerator numeric enrichment now joins `p5st-her9` only through PD_IDs
  already matched by the same-run Current Model Index. It does not participate in
  certification eligibility. The official family rows corroborate all comparable
  selected EnergyGuide values: 48/48 annual-energy and 51/51 capacity values are
  exactly equal. All seven PDP/label capacity differences have EPA equal to the
  label and different from PDP. User direction: missing PDP annual energy is LOW;
  capacity uses exact equality with no tolerance and each confirmed difference is
  MEDIUM. Assessment activation and exact
  issue-code naming remain the next rule step.
  Hosted ubuntu-24.04 run 35564075530 passed at `0719f7e`; artifact
  `g2-label-quality-35564075530-1` (ID 10623360729) preserves the raw EPA
  metadata/rows with SHA-256 records, replayed enrichment, and the three-source
  comparison. The hosted summary confirms EnergyGuide/EPA exact equality for all
  comparable values and shows EPA equal to EnergyGuide for all seven PDP capacity
  differences.
- Refrigerator numeric assessment is active under the approved rules and issue
  codes. `PDP_ANNUAL_ENERGY_MISSING` emits LOW; any exact PDP/EnergyGuide capacity
  difference emits MEDIUM as `PDP_ENERGYGUIDE_CAPACITY_MISMATCH`, with zero
  tolerance. Independent findings are preserved and the highest severity drives
  the SKU display. The 75-SKU result is 31 findings across 29 affected SKUs:
  24 LOW and seven MEDIUM; UI display is 46 PASS, seven MEDIUM and 22 LOW.
  Hosted ubuntu-24.04 run 35564685897 passed at `8a6dcaf`; artifact
  `g2-label-quality-35564685897-1` (ID 10624030788). G1 common-contract regression
  run 35564685890 passed at the same commit. Canonical report integration is next.
- Canonical report integration is complete. The full same-run G2 collector now
  captures p5st numeric evidence only after Current Model Index PD_ID matching,
  replays its raw hashes, applies the numeric assessment, and attaches the
  complete 75-SKU section as `energyguide_numeric` in `report.json`. The section
  rejects an execution-ID, exact-SKU-coverage or display-count mismatch and does
  not enable whole-product compliance. Hosted ubuntu-24.04 run 35566584490 passed
  at `be6277e`; artifact `g2-pilot-35566584490-1` (ID 10624737882) is 51.3 MB.
- The two manually reviewed multi-pattern EnergyGuide labels now have a separate,
  deliberately narrow model-inclusion assessment. It covers only the two
  hash-bound RF90F labels and their six listed SKUs. After approved terminal
  `AA` removal, a SKU is PASS when either explicitly printed pattern matches
  positionally (`*` is exactly one uppercase letter or digit): `RF90F23AEWAA`,
  `RF90F23AECEAA`, `RF90F23AECRAA`, `RF90F29AEWAA`, `RF90F29AECEAA`, and
  `RF90F29AECRAA` all pass. This is not a general wildcard identity rule and
  does not alter numeric LOW or MEDIUM findings. The next step is hosted
  ubuntu-24.04 validation of this canonical-report section. The first hosted
  attempt (run 35571621828) failed because the smoke runner passed the loaded
  SKU-index map where the assessor expected the original review document. The
  runner now keeps both forms and passes the source document to the assessor.
- The canonical refrigerator report now also contains a per-SKU control summary.
  It replays the complete 75-SKU Energy Star publication and numeric sections,
  and adds the six-SKU reviewed model-pattern section only where it applies.
  Each control keeps its own result and all HIGH/MEDIUM/LOW findings are
  retained together; the projection cannot enable overall product compliance.
  It rejects mixed-run inputs, missing SKU coverage and replay-count changes.
  Next: validate this report projection on the GitHub-hosted full G2 run, then
  use it as the stable input for the fixture dashboard.
- A refrigerator fixture dashboard builder now consumes only one same-run bundle
  and canonical report. It emits static run/summary/findings/report-data JSON,
  two reconciled CSV exports and a small filterable HTML view. The builder
  preserves control outputs instead of re-evaluating them, rejects mixed run IDs
  and replay-count drift, and records `NOT_EVALUATED` as the whole-product gate.
  Public compact evidence links and GitHub Pages deployment remain later G2d/G7
  work; this output is an artifact-only fixture dashboard.
- Dashboard-only edits now use the five-minute `g2-dashboard-contracts.yml`
  workflow. Full refrigerator source collection ran as hosted run
  [35604010759](https://github.com/Empty-Bell/RDA/actions/runs/35604010759) and
  passed in 30 minutes. The artifact's report/dashboard consistency acceptance
  was initially part of that full run. It now runs as a separate hosted job that
  downloads a successful `g2-pilot` artifact and validates it offline; hosted
  acceptance run [35608640670](https://github.com/Empty-Bell/RDA/actions/runs/35608640670)
  passed against source run `35604010759`, with no second source collection.
  The full pilot auto-runs on source/assessment changes; direct edits to its
  orchestration script require manual dispatch.

- Dishwasher work has moved to separate GitHub-hosted jobs to keep each source
  step short. Source reconnaissance run `35609221806` passed in about 40 seconds.
  Exact-SKU PDP collection is implemented in `g3-dishwasher-collection.yml` and
  consumes the source-recon artifact; no refrigerator population is revisited.
  EnergyGuide retrieval is implemented in `g3-dishwasher-energyguide-collection.yml`
  and downloads each distinct Support URL once, recording verified PDF SHA-256
  and all SKU/document links. The user confirmed the latest EnergyGuide retrieval
  run succeeded; run-level counts have not yet been inspected in this session.
- Next dishwasher checkpoint: observe each byte-distinct PDF once using PyMuPDF
  embedded text and page coordinates, with RapidOCR fallback only for pages
  lacking embedded text. Preserve raw candidates and layout proposals with a
  2x page preview; expose US `EnergyGuide` and Canadian `EnerGuide` heading
  locations without inferring crop bounds or selecting values. No assessment.
  Recommended implementation model: Terra medium; result review: Luna low.
- After observation, the next short job is `g3-dishwasher-energyguide-review-queue.yml`.
  It reads the observation artifact offline and emits one review row per PDF
  hash with raw annual-energy/model/capacity candidates, US/Canada heading
  candidates, page previews, and exact-SKU membership. Every row remains
  `REVIEW_REQUIRED`; no value is selected and no finding is emitted. It starts
  only from a successful observation `workflow_run` or manual dispatch, so a
  code push cannot race ahead of the first successful observation artifact.
- EPA source capture now runs after successful dishwasher observation through
  `g3-dishwasher-epa-capture.yml`. It stores the official `q8py-6w3f` metadata
  and the current Samsung-filtered rows with raw SHA-256 hashes. It is source
  evidence only; exact model matching, current certification interpretation,
  and assessment are not enabled.

Repository root: C:/Users/JB/Documents/Coding/RDA/repo.
Local Python: runtime/g1-venv/Scripts/python.exe (ignored dev venv).
Local test env PYTHONPATH=src (add scripts for checks/g2).
Hosted G1 CI installs requirements-g1-tools.lock, runs quality.py plus run.py.
Use git safe.directory override. Git write/network may need sandbox escalation.

- G3 clothes-washer source refresh workflow added and completed on hosted
  ubuntu-24.04: run [35680095563](https://github.com/Empty-Bell/RDA/actions/runs/35680095563),
  commit `fad22a7`, artifact `g3-washer-source-35680095563-1` (ID 10675311144).
  Bootstrap, current Samsung source observation, EPA metadata/sample checks and
  artifact upload all passed. Artifact body could not be read via anonymous API,
  so no new population count is asserted here. Next: full exact-SKU washer PDP
  collection from this successful artifact, preserving combo/standalone source
  identity and leaving certification/measurement assessments disabled.

- Washer continuation checkpoint, all on GitHub-hosted `ubuntu-24.04`:
  exact-SKU PDP collection [35681575057](https://github.com/Empty-Bell/RDA/actions/runs/35681575057)
  passed. The collector exits successfully only when every exact SKU in the source
  population has a verified matching PDP URL, current JSON-LD identity and same-SKU
  Specs/Support response. No model/energy assessment ran.
  Parallel source capture [35682498558](https://github.com/Empty-Bell/RDA/actions/runs/35682498558)
  passed both jobs: all declared Samsung Support EnergyGuide URLs were retrieved as
  valid PDFs, and EPA `bghd-e2wd` metadata/schema plus the Samsung current-row scan
  passed count/page/identity stability checks. EnergyGuide result now records an
  explicit per-exact-SKU count, including SKUs with no Support-declared PDF.
  Text/layout/OCR observation [35682719846](https://github.com/Empty-Bell/RDA/actions/runs/35682719846)
  passed for every unique PDF hash; embedded text is preferred and OCR is only the
  unreadable-page fallback. Neither source candidates nor EPA rows have been matched,
  selected or assessed. The raw candidate review queue is wired to run after the
  refreshed observation artifact and will show model text, annual-kWh candidates,
  capacity text and exact-SKU PDF membership before any washer rules are activated.
  Existing no-document and combo/standalone cases remain visible; no appliance
  compliance conclusion is implied by collector success.
  Next: inspect the Washer EnergyGuide raw-candidate review table and establish
  source-backed EPA routing/model/annual-energy comparability, keeping all-in-one
  washer-dryer products distinct until evidence resolves applicability. Do not
  start the unified dashboard until all product-family source/assessment work is
  complete. Recommended model for this fixed-schema evidence review: Luna low;
  use Sol medium only if the source fields require a new comparison policy.

- Washer same-run PDP / EnergyGuide / EPA candidate comparison completed on
  GitHub-hosted `ubuntu-24.04`: [comparison run 35685571247](https://github.com/Empty-Bell/RDA/actions/runs/35685571247), commit `d0baadc`.
  Observation, raw label review, and comparison all passed. The comparison covers
  37 exact PDP SKUs against the linked Samsung Support label PDFs and current
  EPA `bghd-e2wd` rows. It keeps unmodified SKU values, positional wildcard model
  candidates, EPA market text, and raw kWh evidence; EPA energy candidates are
  restricted to rows explicitly listing the US market. No PASS/LOW/HIGH or
  certification finding was generated.
  Source comparison counts: 22 SKUs have one exact equal kWh value in PDP, label,
  and EPA; 2 differ; 13 lack at least one source value/model row. The 2 differing
  SKUs are `WH46DBH500EVA3` and `WH46DBH500GVA3`: PDP says 103 kWh/year while both
  their Support label and EPA current model row say 95 kWh/year. EPA identifies
  both rows as Front Load / Laundry Center, qualified 2023-11-21. This is the
  principal unresolved numeric discrepancy and needs source-field review before
  assessment rules are applied.
  The 13 incomplete rows split into 8 with no current EPA model-pattern row:
  `WA40A3005AW/A4`, `WA41A3000AW/A4`, `WA44A3205AW/A4`, `WA45T3200AW/A4`,
  `WA46CG3505AVA4`, `WA46CG3505AWA4`, `WA47CG3500AVA4`, and `WA47CG3500AWA4`;
  plus 5 where the PDP has no annual kWh candidate although label and EPA agree:
  `WA54CG7105AVUS`, `WA54CG7105AWUS`, `WF90F53ADSA5`, `WF90F53ADYA5`, and
  `WW25FG6B34BEA2`. Every listed SKU still has an exact PDP identity and a
  positional label-model-pattern match. These are source-coverage/comparison
  observations only; no severity is assigned here. Next: inspect the two
  laundry-center PDP field values against their exact PDP/Support evidence and
  confirm the 8 EPA no-row cases against the captured Samsung EPA model list.
  Keep the dashboard deferred until remaining product families are completed.
  Recommended model for this bounded source-review step: Luna low; use Sol medium
  only if the evidence reveals a new rule decision.

- Follow-up Washer source diagnostics completed: [comparison rerun 35686761880](https://github.com/Empty-Bell/RDA/actions/runs/35686761880), commit `40bc389`.
  The 8 EPA no-row SKUs have neither a positional wildcard match nor a match after
  punctuation-only normalization against any of the 66 captured current Samsung
  rows; none has an EPA model candidate sharing even 5 initial alphanumeric
  characters after punctuation is removed. These eight are confirmed absent from
  this captured current cohort under the tested matching methods; no severity has
  been assigned.
  The two numeric conflicts are confirmed at the source-field level: the exact-SKU
  PDP Specs field `Energy Guide Label` says 103 kWh/year; same-PDF printed model
  patterns and yearly-energy text say 95; each matching EPA row says 95. The live
  PDP pages identify the exact SKUs as separate electric-dryer and gas-dryer
  Laundry Center variants. Their PDP identity is not the cause of the discrepancy.
  Remaining determination: decide how the G3 annual-energy comparison should
  classify (a) a PDP-vs-label/EPA value conflict and (b) a product absent from the
  current EPA cohort. The 5 PDP-missing cases have label/EPA agreement and follow
  the already requested LOW treatment once Washer assessment is enabled.

- Washer assessment is now enabled under the approved rules: [hosted run 35687295557](https://github.com/Empty-Bell/RDA/actions/runs/35687295557), commit `b9755d8`.
  All 37 exact SKUs were assessed from the same linked PDP, Support-label and EPA
  artifacts. Display counts are HIGH 0, MEDIUM 2, LOW 5, PASS 30. The two
  Laundry Center PDP-vs-label/EPA annual-energy conflicts are MEDIUM. The five
  SKUs whose PDP annual energy is missing while label and EPA agree are LOW.
  `WF90F53ADYA5` also has an ENERGY STAR publication consistency LOW because EPA
  registration and the spec claim are present while PLP and PDP logos are absent;
  it remains one LOW SKU with two findings.
  The 8 SKUs absent from EPA current have no PLP logo, PDP logo, or spec
  certification claim, so the approved condition “EPA absent + any claim present”
  does not fire and they count as PASS. If a future run observes any of those
  publication points while the model is still absent from EPA current, the same
  rule emits HIGH automatically. No manual override or inferred certification
  state was used. Washer is ready to hand off to the eventual unified dashboard;
  dashboard implementation remains deferred until all product families finish.
  Television full-population chain is now wired: fresh source reconnaissance
  automatically starts exact-SKU PDP capture; a successful PDP run starts
  EnergyGuide PDF retrieval and full EPA TV capture in parallel; their successful
  completion starts OCR observation and a no-grading source-candidate comparison.
  Initial TV exact-SKU PDP run failed after 40m33s: 47/167 verified and 120
  failed. The first recovery finished in about six minutes. Saved evidence shows
  119 PDPs had a valid exact-SKU URL and exact-SKU Specs/Support bridge; they
  failed only because the page also had anonymous Product JSON-LD shells. The
  collector now ignores only those unidentified shells while still rejecting
  conflicting identified SKUs. The remaining SKU `QN100QN80FFXZA` was routed by
  PF once routed `QN100QN80FFXZA` to the `QN115QN90FFXZA` page, but its retry
  then passed; the complete combined artifact is now 167/167 verified. EPA
  capture succeeded. EnergyGuide retrieval reached 162/167 actual PDFs. Five Samsung
  URLs claim `application/pdf` but return 70–79 KB bodies beginning `<## NASC`,
  so they are not accepted as PDF evidence. The collector now records the first
  96 response bytes, requests identity encoding, and retrieves up to eight URLs
  in parallel. The five bodies decode to `NASC A DRM FILE - VER1.00`; MASTER_PLAN §12
  classifies them `NOT_ACCESSIBLE`, HIGH,
  `ENERGYGUIDE_FILE_NOT_READABLE_CANDIDATE`. The 162 readable PDFs continue
  through OCR and same-run candidate comparison; no label values are inferred.
  Diagnostic run: [35692565164](https://github.com/Empty-Bell/RDA/actions/runs/35692565164).
  Bounded source reconnaissance already passed (run 35105667331).
  The approved rules are: comparable annual-energy disagreement = MEDIUM;
  missing PDP annual energy with agreeing label/EPA = LOW; absent EPA current
  model plus any PLP/PDP logo or Spec certification claim = HIGH. TV operating
  power W is retained separately from annual kWh. Recommended model for this
  fixed-schema hosted workflow review: Luna low; runtime itself uses no LLM.
  Business-approved MNA exclusion is implemented and hosted-tested. TV collection
  run 35703343706 (commit 011ee1f) verified 165/165 exact SKUs after excluding
  `MNA101MS1BCXZA` and `MNA89MS1BACXZA`. EnergyGuide/EPA capture 35704036734
  succeeded with 160 readable PDFs, five NASCA DRM labels and passing EPA capture.
  Comparison 35704080904 passed with 165 rows, zero MNA, five
  NOT_ACCESSIBLE/HIGH candidates and 35 unique exact-US-model annual-kWh
  differences at MEDIUM candidate severity. All 35 labels are higher (median
  +17.5%); OCR has one annual candidate and model strings match. There are 130
  models without an exact EPA model row; 59 near-prefixes are diagnostics only.
  W comparisons remain separate: 20 differences, 138 without exact EPA on-mode W,
  seven without PDP typical W. This run is candidate generation, not final product
  grading. The systematic kWh difference may reflect EnergyGuide's DOE represented
  values versus EPA's certified AEC; see TV_SOURCE_CONTRACT for regulatory basis.
  Verify model-level reporting basis before treating the 35 as confirmed defects.
  A duplicate collection was inadvertently started because both push and source-
  recon triggers fired. Commit 7cbab99 removes that duplicate path and prevents a
  skipped recovery job from reporting a false failure.
  Next: validate the 35 candidates against the represented-value/AEC field basis,
  then resolve any remaining EPA identity patterns. Recommended model: GPT-5.6
  Luna low for fixed-schema review; use GPT-5.6 Terra medium only if a data
  definition or severity decision remains.
