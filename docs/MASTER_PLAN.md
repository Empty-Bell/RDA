# US Samsung.com FTC EnergyGuide + EPA ENERGY STAR Audit
## Greenfield Codex Implementation Master Plan

**Status:** Master baseline for clean-room reimplementation  
**Target:** Public GitHub repository + GitHub Pages + GitHub-hosted Actions runner  
**Primary environment:** GitHub Actions on standard GitHub-hosted Ubuntu 24.04 x64 runners, from Phase 0 onward. Personal PC is an optional editing/debugging environment.  
**Implementation style:** Clean-room rewrite. Historical prototypes and internal project artifacts are reference material only.

---

# 0. Project charter

This project automates periodic validation of regulatory disclosure and certification consistency on **Samsung.com US**.

The project has two independent regulatory domains:

1. **FTC / EnergyGuide**
2. **EPA / ENERGY STAR**

The audit must preserve a strict separation between population discovery, Samsung PDP data extraction, EnergyGuide document extraction, EPA certification lookup, rule evaluation, browser-visible evidence, presentation/dashboard rendering, and pipeline health.

The project must never convert parser failure, missing evidence, source ambiguity, or pipeline failure into a PASS.

The project must never use the dashboard layer to invent or modify audit semantics.

The project must never present an automated result as a final legal conclusion.

```text
automatic_final_legal_conclusion = false
```

Target operating principle:

```text
ONE AUDIT RUN
      ↓
ONE CANONICAL PRODUCT POPULATION
      ↓
ONE CANONICAL FACT DATASET
      ↓
ONE RULE EVALUATION
      ↓
ONE PRESENTATION BUILD
      ↓
ONE COHERENT GITHUB PAGES DASHBOARD
```

---

# 1. Confirmed project decisions

- Repository: **public**.
- Production presentation: **GitHub Pages**.
- Primary runner: **standard GitHub-hosted `ubuntu-24.04` x64 runner**. Every phase acceptance requires an actual GitHub Actions run.
- Local personal-PC execution remains supported.
- Runtime baseline: Python 3.12 for audit execution; Python 3.11 compatibility in fixture CI; Node.js 22 where required; headless Playwright Chromium. Install and version-lock dependencies explicitly.
- Cold-start execution must work without a local browser profile, persistent runner state, prewarmed cache, GPU, or Windows dependency.
- No Windows-only production dependency.
- Clean-room rewrite; historical code is reference only.
- DOE is **not** an input/source of truth in this new project.
- Evidence policy: compact public finding evidence on Pages, large/raw evidence in GitHub Actions artifacts.
- Existing HIGH/MEDIUM/LOW semantics and issue priority are preserved.
- ENERGY STAR V1 scope: certification support + claim consistency only; no color/clear-space visual guideline audit.

## 1.1 Product groups

### FTC EnergyGuide + EPA ENERGY STAR
1. Refrigerator
2. Dishwasher
3. Clothes Washer
4. Television

### EPA ENERGY STAR-focused
5. Range
6. Cooktop
7. Clothes Dryer
8. Ventilating Hood
9. Monitor / Display
10. Computer
11. Tablet

---

# 2. Source-of-truth architecture

```text
Samsung PLP pf_search
        ↓
Current product population

Samsung PDP bridge_data
        ↓
PDP structured facts

EnergyGuide PDF
        ↓
Label model + energy values

EPA certified-product API/data
        ↓
Certification model + energy values
```

Playwright is a browser-visible verification and fallback layer, not the primary structured-data source.

---

# 3. Samsung PLP population contract

## 3.1 Primary source: pf_search

For each configured Samsung.com US PLP, Phase 0 must inspect the page network and identify the current `pf_search` endpoint actually used by Samsung.com.

Do not blindly hardcode historical endpoint paths.

Capture and document:

- endpoint,
- HTTP method,
- category/query parameters,
- pagination,
- `startIndex`,
- `requestCount`,
- `searchTotalCount`,
- representative product field,
- representative SKU field,
- family/group identifier,
- `groupedProductList` or equivalent variant collection,
- PDP URL field,
- commerce/stock fields,
- ENERGY STAR PLP observation if present.

Freeze sanitized response fixtures and create contract tests.

## 3.2 Representative vs sub/variant SKU

```text
Product Family / Tile
      ├─ Representative SKU
      └─ Sub / Variant SKUs
```

The audit unit is the **exact SKU**.

Preserve:

```text
family_id
representative_sku
exact_sku
sku_role = REPRESENTATIVE | VARIANT
source_plp
source_pf_search_record
```

## 3.3 Population validation gate

Cross-check:

1. rendered representative tile count,
2. page `N Results` count,
3. `pf_search.searchTotalCount` or current equivalent.

Expected:

```text
rendered representative tiles
=
page result count
=
pf_search total
```

If not:

```text
POPULATION_VALIDATION_FAILED
```

and that family cannot be published as complete.

## 3.4 View More / lazy load

Support:
- View More,
- scrolling,
- repeated pagination,
- lazy loading.

Stop only when:
- no active View More remains,
- repeated rounds add no products,
- final count reconciles.

## 3.5 Population exclusions

Do not auto-add products based only on:
- sitemap,
- guessed URLs,
- historical URLs,
- EPA certification list,
- previous audit history.

Current audit population = current Samsung.com PLP population.

---

# 4. Samsung PDP structured-data contract

## 4.1 Primary source: bridge_data

For each SKU/PDP, inspect the current PDP network flow and identify the current `bridge_data`-type structured endpoint.

Contract must identify:
- endpoint,
- request key/SKU,
- model field,
- PDP URL identity,
- title,
- commerce state,
- spec-table structure,
- EnergyGuide document collection,
- EnergyGuide PDF URL,
- ENERGY STAR structured flags,
- ENERGY STAR spec field,
- variant metadata if present.

Capture family fixtures and contract-test them.

## 4.2 Canonical PDP fields

```text
family
exact_sku
pdp_model
pdp_url
product_title
commerce_status
stock_flag
ecom_flag
pdp_annual_energy_kwh
pdp_capacity
pdp_other_energy_fields
energyguide_document_name
energyguide_document_type
energyguide_url
plp_energy_star_claim
pdp_structured_energy_star_claim
pdp_spec_energy_star_claim
```

Do not collapse ENERGY STAR claim sources during extraction.

## 4.3 Spec aliases

Family adapters normalize raw labels:

```text
"Energy Consumption"
"Annual Energy Consumption"
"Energy Consumption (kWh/year)"
        ↓
annual_energy_kwh
```

Core rule logic uses normalized fields only.

## 4.4 PDP identity gate

Valid PDP requires structured/rendered model support for target SKU.

Invalid:
- PLP redirect,
- support page,
- warranty page,
- search page,
- different rendered SKU,
- different structured SKU.

URL text alone is never sufficient.

---

# 5. Structured fallback hierarchy

Primary:

```text
pf_search   → population
bridge_data → PDP facts
```

Historical `__NEXT_DATA__` and variant-click Playwright may be used only as fallback/cross-check after current reconnaissance.

Priority:

```text
structured source
→ browser/network observation
→ controlled UI interaction
→ URL guessing last
```

---

# 6. EnergyGuide document acquisition

## 6.1 URL provenance

Primary: PDP `bridge_data` document metadata.  
Secondary: rendered PDP EnergyGuide link verification.

DOE EnergyGuide URL is not used in this new project.

## 6.2 Download validation

Record:
- requested URL,
- final URL,
- status,
- Content-Type,
- PDF signature,
- size,
- SHA-256,
- timestamp.

Statuses:

```text
PDF_OK
LABEL_URL_NOT_PDF
HTTP_ERROR
EMPTY_FILE
INVALID_PDF_SIGNATURE
DOWNLOAD_TIMEOUT
DOCUMENT_MISSING
```

HTTP 200 does not mean valid PDF.

---

# 7. PDF text extraction architecture

This section is mandatory.

## 7.1 Extraction order

```text
EnergyGuide PDF
      ↓
PyMuPDF embedded/block text
      ↓
text quality gate
      ├─ PASS → field parser
      └─ FAIL → RapidOCR fallback
```

Primary = **PyMuPDF**.  
Fallback = **RapidOCR**.

Never reverse this order.

## 7.2 PyMuPDF quality gate

Fallback to OCR when one or more are true:

- empty text,
- text too short,
- EnergyGuide marker words missing,
- model field not extractable,
- annual kWh not extractable,
- required family fields incomplete,
- text/layout clearly corrupted.

Record:

```text
ocr_fallback_reason
```

Values may include:

```text
EMPTY_EMBEDDED_TEXT
SHORT_EMBEDDED_TEXT
ENERGYGUIDE_MARKERS_MISSING
MODEL_FIELD_MISSING
KWH_FIELD_MISSING
REQUIRED_FIELDS_INCOMPLETE
TEXT_CORRUPTED
```

## 7.3 RapidOCR baseline optimization

Preserve these settings/behaviors:

- instantiate RapidOCR once per run/worker,
- reuse engine across documents,
- conservative ONNX/OpenCV threading,
- baseline thread settings: **1 / 1**,
- default PDF render: **2×**,
- full-page OCR first,
- model/wildcard targeted retry only when needed,
- model/wildcard retry render: **3×**,
- ROI crop,
- grayscale,
- Otsu binarization,
- OCR ROI,
- preserve full-page and retry outputs.

No Windows OCR / WinRT dependency.

## 7.4 Difficult low-resolution labels

The 2×/3× path is the baseline.

For difficult low-resolution labels, 300–600 DPI-equivalent ROI rendering may be benchmarked, but production changes require:
- fixtures,
- before/after metrics,
- documented decision.

## 7.5 CTC wildcard caveat

RapidOCR/CTC decoding can collapse repeated tokens such as `****`.

Therefore:
- never rely only on OCR to count repeated `*`,
- preserve image evidence,
- use model-pattern context,
- ROI retry,
- PDP/EPA identity corroboration,
- unresolved wildcard extraction gets its own review state.

## 7.6 Raw vs interpreted output

Never overwrite raw OCR results.

Store:

```text
raw_text
raw_model_candidate
raw_kwh_candidate
raw_capacity_candidate
normalized_model_candidate
normalized_kwh
normalized_capacity
correction_applied
correction_type
correction_reason
ocr_engine
ocr_scale
ocr_roi_used
```

---

# 8. OCR character-confusion reconciliation

## 8.1 Known pairs

At minimum:

```text
8 ↔ B
0 ↔ O
1 ↔ I
1 ↔ l
5 ↔ S
```

Do not globally replace characters.

## 8.2 Candidate-equivalence logic

First exact-normalize and compare.

If mismatch remains, identify whether differences are limited to known OCR-confusion positions.

Example:

```text
PDP: RF28B...
OCR: RF288...
```

This is a confusion candidate, not immediately a mismatch.

## 8.3 Cross-field corroboration

A correction may be accepted when independent evidence agrees:

- all non-confusion model characters match,
- same model structure/length,
- PDP kWh = EnergyGuide kWh,
- EPA kWh = same value when EPA exists,
- capacity matches when applicable,
- other family-specific numeric fields match,
- document URL belongs to same target SKU,
- EPA model/pattern supports corrected identity.

Principle:

```text
one ambiguous OCR character
+
all independent identity/value evidence agrees
=
do not classify as model mismatch
```

## 8.4 Outcomes

### Confidently corrected

```text
ENERGYGUIDE_OCR_MODEL_CHAR_CORRECTED
severity = none/informational
```

Not a compliance finding.

### Plausible but unresolved

```text
ENERGYGUIDE_OCR_MODEL_CHAR_SUSPECT
severity = MEDIUM
```

### Genuine mismatch

Only when ambiguity-aware reconciliation fails or independent evidence contradicts equivalence.

## 8.5 Example

```text
PDP model        RF28B1234SRAA
PDF OCR model    RF2881234SRAA
PDP kWh          685
PDF kWh          685
EPA model        RF28B1234****
EPA kWh          685
```

Result:

```text
B↔8 strongly corroborated
→ ENERGYGUIDE_OCR_MODEL_CHAR_CORRECTED
→ not mismatch
```

Counterexample:

```text
PDP model        RF28B1234SRAA
PDF OCR model    RF2889234SRAA
PDP kWh          685
PDF kWh          702
```

Result: not safely explainable by one confusion; proceed to mismatch/review rules.

---

# 9. EnergyGuide field extraction

Minimum:

```text
label_model
annual_energy_kwh
capacity when applicable
```

Pipeline:

```text
raw text
→ candidate extraction
→ normalization
→ field validation
→ cross-source reconciliation
```

Extraction and compliance decision are separate functions/modules.

---

# 10. Three-source reconciliation

For applicable families:

| Source | Model | Annual Energy |
|---|---|---|
| Samsung PDP / bridge_data | PDP model | PDP kWh |
| EnergyGuide PDF | label model | label kWh |
| EPA API if available | EPA model/pattern | EPA kWh |

Independent comparisons:

```text
PDP Model         ↔ EnergyGuide Model
PDP kWh           ↔ EnergyGuide kWh
PDP Model         ↔ EPA Model
PDP kWh           ↔ EPA kWh
EnergyGuide Model ↔ EPA Model
EnergyGuide kWh   ↔ EPA kWh
```

EPA absence alone is not an FTC failure.

---

# 11. EPA ENERGY STAR contract

Phase 0 identifies current official certified-product dataset/API per family.

Record:
- dataset ID,
- endpoint,
- brand field,
- model field,
- UPC if available,
- annual-energy field if applicable,
- market field,
- certification/status field,
- retrieval timestamp.

Architecture:

```text
EPA common client
      ↓
family-specific adapter
```

Baseline matching hierarchy:

1. exact/current model-pattern support,
2. exact UPC support,
3. prefix + kWh candidate,
4. no current candidate.

Possible states:

```text
CURRENT_EPA_EXACT_PATTERN_MATCH
CURRENT_EPA_EXACT_UPC_MATCH
EPA_UPC_AMBIGUOUS_MANUAL_REVIEW
CURRENT_EPA_PREFIX_AND_KWH_CANDIDATE_MANUAL_VARIANT_REVIEW
NO_CURRENT_EPA_CANDIDATE
```

Observe claims independently:

```text
PLP claim
PDP structured claim
PDP spec claim
rendered badge
```

No EPA candidate by itself is not a finding.

Potential eligibility issue requires public claim + no supported current EPA certification.

---

# 12. Baseline issue priority and severity

Preserve this rule priority:

1. missing EnergyGuide document  
   HIGH → `ENERGYGUIDE_DOCUMENT_MISSING_CANDIDATE`

2. wrong document  
   HIGH → `ENERGYGUIDE_WRONG_DOCUMENT_CANDIDATE`

3. confidently wrong model label  
   HIGH → `CRITICAL_WRONG_MODEL_LABEL_CANDIDATE`

4. OCR model confusion corrected  
   informational → `ENERGYGUIDE_OCR_MODEL_CHAR_CORRECTED`

5. OCR model char suspect  
   MEDIUM → `ENERGYGUIDE_OCR_MODEL_CHAR_SUSPECT`

6. label inaccessible/unreadable  
   HIGH → `ENERGYGUIDE_FILE_NOT_READABLE_CANDIDATE`

7. ENERGY STAR claim + no current EPA candidate  
   HIGH → `CRITICAL_ENERGY_STAR_ELIGIBILITY_CANDIDATE`

8. Samsung ENERGY STAR source conflict  
   LOW → `SAMSUNG_ENERGY_STAR_SOURCE_CONFLICT`

9. claim + unresolved EPA variant identity  
   MEDIUM → `ENERGY_STAR_VARIANT_IDENTITY_REVIEW`

10. OCR fields incomplete: kWh  
    MEDIUM → `ENERGYGUIDE_KWH_NOT_EXTRACTED`

11. OCR fields incomplete: model wildcard  
    MEDIUM → `ENERGYGUIDE_MODEL_WILDCARD_NOT_EXTRACTED`

12. otherwise no automated exception.

Unit-test the exact priority order.

---

# 13. Domain separation

## FTC / EnergyGuide
Use:
- document presence,
- accessibility,
- document/model identity,
- PDP model,
- label model,
- PDP/label kWh,
- capacity/applicable values,
- OCR quality.

EPA status does not decide whether the EnergyGuide label itself is correct.

## EPA / ENERGY STAR
Use:
- Samsung public claim,
- current EPA certified-product data,
- model/UPC/prefix matching,
- compatible energy field,
- source consistency.

EnergyGuide OCR failure does not become EPA failure.

Both domains may yield issues for one SKU.

---

# 14. Browser audit

Playwright is used for:
- rendered ENERGY STAR badge,
- rendered EnergyGuide link,
- structured/rendered discrepancy,
- browser-only identity fallback,
- diagnostic inspection.

V1 excludes mark color/clear-space geometry.

Browser statuses:

```text
PASS
PARTIAL
ERROR
NOT_APPLICABLE
```

`automatic_final_legal_conclusion=false` is governance metadata, never a finding trigger.

---

# 15. Canonical schemas

## RunManifest

```text
schema_version
run_id
started_at
completed_at
git_sha
config_hash
rule_version
source_contract_version
python_version
playwright_version
runner
overall_execution_status
```

Recommended run ID:

```text
YYYYMMDDTHHMMSSZ_<gitsha7>
```

## ProductPopulationRecord

```text
family
family_code
family_id
representative_sku
exact_sku
sku_role
plp_url
pdp_url
commerce_status
stock_flag
ecom_flag
variant_attributes
source_pf_search_hash
```

## PdpFactRecord

```text
family
exact_sku
pdp_model
pdp_url
product_title
pdp_annual_energy_kwh
pdp_capacity
energyguide_url
plp_energy_star_claim
pdp_structured_energy_star_claim
pdp_spec_energy_star_claim
source_bridge_hash
```

## EnergyGuideExtractionRecord

```text
exact_sku
document_url
document_sha256
document_status
extraction_engine
embedded_text
ocr_raw_text
label_model_raw
label_model_normalized
annual_energy_kwh
capacity
model_confusion_detected
model_confusion_corrected
correction_reason
fallback_reason
ocr_scale
ocr_roi_used
```

## EpaRecord

```text
family
dataset_id
epa_unique_id
model_number
upc
annual_energy_kwh
markets
certification_status
retrieved_at
source_hash
```

## AssessmentRecord

```text
run_id
family
exact_sku
regulatory_domain
control_id
rule_id
rule_version
assessment_status
severity
issue_code
reason
expected
observed
evidence_ids
automatic_final_legal_conclusion
```

---

# 16. Status model

Compliance/evaluation:

```text
NO_EXCEPTION_OBSERVED
FINDING
REVIEW_REQUIRED
NOT_APPLICABLE
NOT_EVALUATED
```

Pipeline execution:

```text
SUCCESS
PARTIAL
FAILED
OUTPUT_MISSING
```

Unknown/unprocessed is never PASS.

---

# 17. Evidence strategy

Public compact Pages evidence:

```text
site/evidence/<run_id>/<family>/<sku>/
    finding.json
    comparison.json
    extracted_values.json
    manifest.json
```

Large/raw Actions artifact:

```text
raw_evidence/
    PDP HTML
    original EnergyGuide PDF
    OCR render/ROI images
    screenshots
    raw pf_search response
    raw bridge_data response
    raw EPA response
```

Manifest fields:

```text
source_url
captured_at
sha256
parser_version
run_id
family
sku
evidence_type
```

---

# 18. History

Finding key:

```text
family + exact_sku + issue_code
```

States:

```text
NEW
OPEN
RESOLVED
REOPENED
```

Keep:

```text
first_seen
latest_seen
resolved_at
```

History never overrides current evidence.

---

# 19. Presentation model

Human-readable mappings live outside the audit engine.

One canonical mapping:

```text
issue_code
→ control
→ title
→ explanation
→ recommended action
→ evidence fields
→ highlight fields
```

Preserve the concepts historically called:

```text
CONTROLS
ISSUE_TO_CONTROL
ISSUE_META
ISSUE_HIGHLIGHT
```

Do not encode these semantics in HTML/JS.

---

# 20. Dynamic Dashboard Product & Data Specification

The dashboard is not a manually maintained report. It is a **data-driven static application** rebuilt from the current validated run and published to GitHub Pages.

The word "dynamic" has two meanings in this project:

1. **Build-time dynamic generation**  
   Every run recomputes all dashboard sections from canonical JSON. No count, SKU, run number, queue item, KPI, heatmap cell, or product-group status is hand-coded.

2. **Client-side interactive behavior**  
   The generated static site supports filtering, searching, expanding findings, changing views, and drilling into evidence without a backend.

The architecture is:

```text
validated current-run audit records
        +
history/current-vs-previous-run records
        +
presentation mapping
        ↓
dashboard data builder
        ↓
site/data/*.json
        ↓
full static site build
        ↓
GitHub Pages
        ↓
client-side search/filter/drill-down
```

Forbidden:

- regex patching of a previous `index.html`,
- hardcoded run numbers,
- hardcoded current counts,
- hardcoded Action Queue items,
- independent stale dashboard datasets,
- mixing data from multiple run IDs,
- JavaScript re-implementing audit semantics.

The browser may derive presentation-only views, but it must never reinterpret audit rules.

---

## 20.1 Dashboard mental model

The dashboard must answer three questions in order.

```text
Executive / manager
"Is action required right now?"
        ↓
QA owner
"Which product group and control is causing it?"
        ↓
Investigator
"Which exact SKU/value/evidence proves it?"
```

The first screen should answer:

> **Is anything wrong, where is it wrong, and what changed since the previous run?**

A user should not have to inspect crawler logs or raw CSV files to answer those questions.

---

## 20.2 Dynamic dashboard source datasets

Generate a single coherent dashboard data package per run.

Recommended files:

```text
site/data/
    run.json
    summary.json
    family_summary.json
    control_matrix.json
    findings.json
    report_data.json
    delta.json
    history.json
    audit_health.json
    methodology.json
```

These files are all generated from the same `run_id`.

### `run.json`

```json
{
  "run_id": "20260916T120000Z_abc1234",
  "git_sha": "abc1234",
  "started_at": "...",
  "completed_at": "...",
  "rule_version": "...",
  "source_contract_version": "...",
  "runner": "github-hosted"
}
```

### `summary.json`

Contains only values derived from canonical current-run records.

```text
models_in_scope
models_evaluated
ftc_targets
epa_targets
high_count
medium_count
low_count
pipeline_error_count
review_required_count
families_affected
coverage
compliance_gate
```

### `family_summary.json`

One row for each configured family:

```text
family
models_in_scope
models_evaluated
ok
high
medium
low
pipeline_errors
coverage
ftc_applicable
ftc_status
epa_applicable
epa_status
```

### `findings.json`

Actionable exceptions only.

Each record contains canonical audit identity plus presentation metadata:

```text
finding_id
family
sku
severity
regulatory_domain
control
issue_code
title
why
action
expected
observed
evidence_fields
highlight_fields
first_seen
latest_seen
history_state
pdp_url
energyguide_url
public_evidence_url
```

### `report_data.json`

Complete model-level audit data for reporting/export, not just findings.

This is the canonical downloadable/reporting table used for:

- full audit CSV export,
- full audit Excel-compatible export if implemented,
- model search,
- family drill-down,
- QA verification,
- audit traceability.

Recommended fields:

```text
run_id
family
representative_sku
sku
sku_role
pdp_url
commerce_status

pdp_model
pdp_kwh
pdp_capacity

energyguide_status
energyguide_url
energyguide_extraction_engine
label_model_raw
label_model_normalized
label_kwh
label_capacity
ocr_confusion_corrected

epa_status
epa_model
epa_kwh
epa_match_basis

plp_energy_star_claim
pdp_structured_energy_star_claim
pdp_spec_energy_star_claim
browser_energy_star_badge

review_status
severity
issue_code
pipeline_status
```

This file must not independently recalculate severity; it serializes the already-assessed canonical records.

---

## 20.3 Header / navigation

The page header should remain compact.

Display:

```text
US Regulatory Disclosure Audit
main / production
Run <run_id or friendly run sequence>
Last completed <timestamp>
```

Optional actions:

- View GitHub Actions run
- Download Findings CSV
- Download Full Report CSV
- Methodology
- Run History

All displayed run metadata must come from `run.json`.

No run number or timestamp may be embedded manually in template HTML.

---

## 20.4 Hero / Compliance Gate

The Hero is the most important section.

It must visually separate:

```text
page identity
```

from:

```text
current compliance state
```

Suggested layout:

```text
US Samsung.com Regulatory Disclosure Audit

COMPLIANCE GATE

ACTION REQUIRED
19 high-confidence findings are currently open.

19 HIGH      20 MEDIUM      6 LOW
Coverage 99.x%

Run ...
Last completed ...
```

### Gate calculation

The exact gate semantics must be centralized in the dashboard data builder.

Baseline concept:

```text
if HIGH > 0:
    ACTION_REQUIRED
elif MEDIUM > 0 or pipeline_errors > 0:
    REVIEW_REQUIRED
else:
    PASS
```

If the approved existing semantics define the gate as "any open finding", implement that approved definition instead. Do not let front-end JavaScript invent the rule.

### Hero constraints

- Do not lead with pass rate.
- Do not show 99% green in a way that visually overwhelms an open HIGH finding.
- HIGH, MEDIUM, LOW, and pipeline errors are separate concepts.
- Pipeline error never becomes a compliance finding.
- Always display status text in addition to color.

Recommended states:

```text
PASS
ACTION REQUIRED
REVIEW REQUIRED
INCOMPLETE / AUDIT ERROR
```

---

## 20.5 Summary KPI section

Use 5–7 primary KPI cards. Avoid dashboard clutter.

Recommended primary KPIs:

1. **Models In Scope**
2. **Models Evaluated**
3. **FTC Targets**
4. **EPA Targets**
5. **HIGH Findings**
6. **Review Required / MEDIUM**
7. **Audit Coverage**

Secondary/optional:

- LOW findings
- Pipeline errors
- New findings
- Resolved findings
- Affected product groups

### KPI derivation

Every KPI must be a pure aggregation of canonical current-run records.

Examples:

```text
Models In Scope
= count(unique exact SKU in validated current population)

Models Evaluated
= count(SKU with completed applicable assessment)

FTC Targets
= count(SKU in FTC-applicable families)

EPA Targets
= count(SKU in EPA-applicable families)

HIGH
= count(assessment severity == HIGH)

Coverage
= successfully_evaluated / models_in_scope
```

No KPI is manually supplied by HTML.

KPI reconciliation tests must prove:

```text
OK + HIGH + MEDIUM + LOW + non-evaluable/pipeline states
reconcile to the defined model-level population
```

The precise reconciliation formula must be documented if one SKU may have multiple findings.

---

## 20.6 Since Previous Run

Scheduled monitoring must explain change, not only current state.

Show:

```text
new findings
resolved findings
reopened findings
new review cases
new models
removed models
new pipeline failures
```

Example:

```text
Since previous run

+2 new HIGH findings
1 finding resolved
1 finding reopened
34 newly discovered SKUs
2 new pipeline warnings
```

Data comes from `delta.json`.

Do not calculate lifecycle history in JavaScript.

History identity:

```text
family + sku + issue_code
```

---

## 20.7 Product Group Status Matrix

Show all 11 families in one compact table.

Recommended columns:

| Product Group | Models | Evaluated | FTC EnergyGuide | EPA ENERGY STAR | H | M | L | Coverage |
|---|---:|---:|---|---|---:|---:|---:|---:|

Family domain state values:

```text
PASS
FINDING
REVIEW
ERROR
N/A
```

Status precedence within one regulatory domain:

```text
ERROR if domain could not be reliably evaluated
otherwise FINDING if HIGH/open confirmed candidate exists
otherwise REVIEW if MEDIUM/manual-review case exists
otherwise PASS
N/A if family not subject to that audit domain
```

If approved semantics differ, document them centrally.

The matrix must make the 4 FTC+EPA families vs 7 EPA-focused families obvious.

Clicking a family should filter:

- heatmap,
- Action Queue,
- Report Data,

to that family.

---

## 20.8 Regulatory Control Heatmap

This is a primary diagnostic section.

Rows:

```text
11 product groups
```

Columns:

```text
normalized audit controls
```

Recommended control concept for V1:

### FTC / EnergyGuide

```text
Label Present
Label Accessible
Correct Document
Model Match
Energy / kWh Match
```

Capacity/value match can be included as a separate control when applicable and reliable.

### EPA / ENERGY STAR

```text
EPA Registration / Certification
Model Identity
Energy Value Match where applicable
Samsung Claim Consistency
```

The exact normalized columns must be derived from `controls.yaml`.

Each cell state:

```text
PASS
FINDING
REVIEW
ERROR
N/A
```

Color semantics:

```text
green = PASS
red = FINDING
amber = REVIEW
gray = N/A
error treatment = explicit neutral/error styling, not compliance red
```

Always render a text/icon state; color alone is insufficient.

### Heatmap interaction

Clicking a cell such as:

```text
Refrigerator × Model Match
```

must set Action Queue filters:

```text
family = Refrigerator
control = Model Match
severity = ALL
search = empty
```

and scroll/focus to Action Queue.

The heatmap must never contain hand-authored cells.

`control_matrix.json` is derived from assessment records.

---

## 20.9 Action Queue

The Action Queue is the operational triage view.

Default population:

```text
open actionable findings/reviews only
```

Do not show every PASS record in the main queue.

Default ordering:

```text
HIGH
→ MEDIUM
→ LOW
→ newest/reopened
→ family/SKU stable order
```

Recommended filters:

- severity: ALL / HIGH / MEDIUM / LOW
- family
- regulatory domain: FTC / EPA
- control
- history state: NEW / OPEN / REOPENED
- model/SKU search

Search should match at least:

```text
SKU
family
issue title
control
issue_code
```

### Queue row summary

Collapsed row:

```text
Severity
SKU
Product Group
Regulation
Control
Issue Title
First Seen / NEW badge
```

### Expanded finding content

When opened, show:

1. **What was found**
2. **Recommended action**
3. **Observed evidence**
4. **Comparison**
5. **Links**

Evidence examples:

```text
PDP Model
EnergyGuide Model
EPA Model

PDP kWh
EnergyGuide kWh
EPA kWh

PDP Capacity
EnergyGuide Capacity

PLP E-STAR
PDP Structured E-STAR
PDP Spec E-STAR
Rendered E-STAR Badge

EnergyGuide Status
EPA Match Status
OCR Engine
OCR Correction
```

Only fields relevant to the issue need to be prominent.

`ISSUE_HIGHLIGHT`-equivalent mapping controls red/bold emphasis of problem fields.

### Queue links

Where available:

- Open Samsung PDP
- Open public EnergyGuide PDF
- Open compact evidence bundle

Never render a dead evidence link.

Evidence link must only exist if the referenced generated file exists.

### Queue data rule

The queue is derived from current `findings.json`.

It must never be maintained as an independent stale literal.

---

## 20.10 Finding detail / evidence drill-down

A finding drawer, modal, or detail page should show:

```text
SKU
Product Group
Regulatory Domain
Control
Severity
Issue Code
Title

What was found
Expected
Observed

PDP facts
EnergyGuide facts
EPA facts

OCR raw model
OCR normalized model
OCR correction reason if any

First Seen
Latest Seen
History State
Run ID

PDP link
EnergyGuide link
Compact evidence link

Recommended action
```

Important for OCR-corrected cases:

The detail should clearly distinguish:

```text
raw OCR value
normalized/corrected interpretation
correction reason
corroborating fields
```

so a user can audit why `B↔8`, `O↔0`, etc. was not treated as a mismatch.

---

## 20.11 Report Data section

The dashboard must include a full model-level report view separate from the Action Queue.

Purpose:

```text
Action Queue = exceptions
Report Data  = complete audit population
```

This section allows QA to verify all models, including PASS rows.

Recommended columns:

```text
Product Group
Representative SKU
Exact SKU
Role
PDP Status
PDP Model
PDP kWh
EnergyGuide Status
Label Model
Label kWh
EPA Status
EPA Model
EPA kWh
FTC Result
EPA Result
Severity
Issue Code
Pipeline Status
```

Features:

- family filter,
- status/severity filter,
- representative/variant filter,
- model search,
- sorting,
- pagination or virtualized display if needed,
- CSV export.

The page may initially render a summary subset and load `report_data.json` on demand to reduce first-load size.

### Export rules

Generate at build time:

```text
findings.csv
report_data.csv
```

Optional:

```text
report_data.xlsx
```

If XLSX is implemented, generate it in Python; do not fake XLSX by saving HTML as `.xls`.

CSV/export row counts must reconcile with source JSON.

---

## 20.12 Run History / Trend

Use 6–12 recent validated runs.

Recommended metrics:

- HIGH
- MEDIUM
- LOW
- pipeline errors
- coverage
- models in scope

Trend is diagnostic, not decorative.

Avoid:
- pie charts for everything,
- oversized charts,
- visual noise.

Clicking a run may show summary metadata, but the main GitHub Pages site represents the latest validated run unless an explicit historical-run page is implemented.

---

## 20.13 Audit Health

Compliance and pipeline reliability must remain separate.

Show:

```text
families successful
families partial/failed
population validation failures
pf_search parser failures
bridge_data parser failures
EnergyGuide download failures
PyMuPDF extraction fallback rate
RapidOCR failure rate
EPA source failures
browser audit failures
```

Useful OCR metrics:

```text
PyMuPDF direct extraction count
RapidOCR fallback count
RapidOCR fallback %
OCR corrected character count
OCR suspect count
OCR hard failure count
```

A degraded audit should be visible even if no compliance finding was emitted.

---

## 20.14 Methodology

Expose enough methodology so a viewer can understand the result.

Include:

- 11 product-group scope,
- FTC vs EPA applicability,
- `pf_search` population principle,
- `bridge_data` PDP source principle,
- EnergyGuide PDF source,
- PyMuPDF → RapidOCR extraction strategy,
- OCR confusion reconciliation concept,
- EPA matching hierarchy,
- rule version,
- source-contract version,
- known limitations,
- `automatic_final_legal_conclusion = false`.

Do not expose private credentials or internal-only implementation details.

---

## 20.15 Dynamic filtering state

Filters should be shareable within the page state if practical.

At minimum maintain one centralized client-side filter state:

```text
family
severity
domain
control
history_state
query
```

The Heatmap, Product Group Matrix, Action Queue, and Report Data should use compatible filter semantics.

Do not duplicate different filtering implementations that interpret family/control names differently.

---

## 20.16 Build-time derivation rules

The Python dashboard builder, not browser JavaScript, owns:

```text
compliance_gate
KPI counts
family domain status
heatmap cell status
finding presentation metadata
run delta
history state
report export datasets
```

JavaScript owns only:

```text
render
filter
search
sort
expand/collapse
client-side navigation
```

This prevents front-end logic from becoming a second audit engine.

---

## 20.17 Dashboard data consistency gate

Before publishing, validate:

```text
all site/data files share same run_id

summary.models_in_scope
== expected current population

sum family_summary.models_in_scope
== summary.models_in_scope

findings count
== severity/findings aggregation

report_data row count
== expected exact-SKU population or documented evaluable population

all finding SKUs exist in report_data

all heatmap controls exist in controls configuration

all family rows exist exactly once

all evidence URLs point to generated files or external valid source URLs

run metadata displayed in HTML
== run.json
```

Any mismatch = build failure.

---

## 20.18 Front-end technical choice

V1 should prefer:

```text
static HTML
CSS
vanilla JavaScript
generated JSON
```

A framework is optional, not required.

Do not introduce React/Vue/backend infrastructure unless the size or interaction model proves it necessary.

Initial objective:

> Reliable regulatory audit visibility, not front-end sophistication.

---

## 20.19 Visual direction

Target:

- polished technical/compliance console,
- white/light-gray background,
- strong typography,
- spacious hero,
- dense but readable tables below,
- minimal decoration,
- restrained color.

Status colors:

```text
Red    = HIGH / Action Required
Amber  = Review / MEDIUM
Green  = Pass
Gray   = N/A / neutral
Blue   = informational/navigation
```

Never use color without text.

Avoid:
- decorative gradients,
- excessive KPI cards,
- giant pass-rate visuals,
- large empty charts,
- stale hardcoded copy.

---

## 20.20 Dashboard acceptance tests

Fixture-based dashboard tests must assert:

```text
Hero gate matches summary data
Hero run ID matches run.json
KPI values match canonical aggregation
11 family rows render
FTC N/A correctly appears for EPA-only families
Heatmap dimensions match configured families × controls
Heatmap click applies correct queue filter
Queue count matches findings.json
Search filters correct SKU
Severity filter works
Family filter works
Control filter works
Expand/collapse works
Report Data count matches report_data.json
Findings CSV row count matches findings.json
Report CSV row count matches report_data.json
No stale run ID exists in generated site
No broken compact-evidence link is emitted
```

Browser smoke test should confirm:

```text
no red console error
all core sections visible
interactive filters functional
mobile layout remains usable
```

---
# 21. Repository structure

```text
samsung-us-regulatory-audit/
├─ AGENTS.md
├─ README.md
├─ pyproject.toml
├─ package.json
├─ .gitignore
├─ .env.example
├─ configs/
│  ├─ families.yaml
│  ├─ sources.yaml
│  ├─ controls.yaml
│  ├─ presentation.yaml
│  └─ runtime.yaml
├─ docs/
│  ├─ PROJECT_CHARTER.md
│  ├─ MASTER_PLAN.md
│  ├─ SAMSUNG_SOURCE_CONTRACTS.md
│  ├─ EPA_SOURCE_CONTRACTS.md
│  ├─ OCR_CONTRACT.md
│  ├─ AUDIT_RULES.md
│  ├─ DATA_CONTRACTS.md
│  ├─ PIPELINE.md
│  ├─ TEST_STRATEGY.md
│  ├─ RUNBOOK.md
│  ├─ DECISIONS.md
│  └─ adr/
├─ src/regaudit/
│  ├─ cli.py
│  ├─ config.py
│  ├─ models/
│  ├─ sources/
│  │  ├─ samsung/
│  │  │  ├─ pf_search.py
│  │  │  └─ bridge_data.py
│  │  └─ epa/
│  ├─ discovery/
│  ├─ extraction/
│  ├─ ocr/
│  ├─ matching/
│  ├─ rules/
│  │  ├─ ftc/
│  │  └─ epa/
│  ├─ browser/
│  ├─ consolidation/
│  ├─ evidence/
│  ├─ history/
│  ├─ presentation/
│  └─ utils/
├─ dashboard/
│  ├─ templates/
│  ├─ static/
│  └─ build.py
├─ tests/
│  ├─ unit/
│  ├─ contract/
│  ├─ fixtures/
│  ├─ integration/
│  └─ e2e/
├─ runtime/
└─ .github/workflows/
   ├─ ci.yml
   ├─ smoke-audit.yml
   ├─ full-audit.yml
   └─ pages.yml
```

---

# 22. Codex operating rules

`AGENTS.md` must state:

1. Read contracts before editing.
2. Never infer undocumented audit semantics.
3. Ask user if a real semantic ambiguity remains.
4. Do not change rules just to pass tests.
5. Do not mix audit-semantic and dashboard-only changes.
6. No destructive `git reset --hard`/`git clean`.
7. Never copy proprietary internal source.
8. Never hardcode product counts/run numbers.
9. No new issue code without approval.
10. Pipeline error never becomes PASS.
11. Preserve raw evidence before correction.
12. Every external parser requires fixture + contract test.
13. Every rule requires unit tests.
14. Every phase ends PASS/FAIL/BLOCKED.

---

# 23. Implementation phases

## Phase 0 — Reconnaissance
Create the Actions execution foundation first:
- shared bootstrap on `ubuntu-24.04` x64,
- manual `runner-probe.yml`,
- explicit Python/browser/OCR dependency installation,
- cold-cache embedded-text PDF and image-only PDF checks,
- headless Chromium launch and external-source probes,
- uploaded probe logs and sanitized fixtures with Actions run URL.

Local success is diagnostic only. Do not pass Phase 0 or move into production implementation while hosted-runner access/runtime checks remain unverified.

Verify:
- current `pf_search`,
- current `bridge_data`,
- current EnergyGuide fields,
- current EPA datasets,
- GitHub-hosted runner access,
- Playwright.

Deliver:
- `SAMSUNG_SOURCE_CONTRACTS.md`,
- `EPA_SOURCE_CONTRACTS.md`,
- fixtures,
- open questions.
- `GITHUB_HOSTED_RUNNER_CONTRACT.md` and hosted-runner acceptance record.

No decision engine yet.

## Phase 1 — Schemas / skeleton
Implement:
- typed models,
- config,
- run/evidence manifests,
- CLI skeleton,
- fixtures,
- schema tests.
- `ci.yml` executing fixture tests on hosted Ubuntu from this phase onward.

## Phase 2 — Refrigerator vertical slice

```text
pf_search
→ exact SKU
→ bridge_data
→ EnergyGuide URL
→ PDF validation
→ PyMuPDF
→ RapidOCR fallback
→ OCR reconciliation
→ EPA
→ FTC/EPA rules
→ evidence
→ dashboard
```

Do not expand until it passes.
The slice, OCR regression suite, evidence packaging, and complete refrigerator population must pass on GitHub-hosted Ubuntu, not only locally. Add manual smoke execution during this phase.

## Phase 3 — Other FTC+EPA
- Dishwasher
- Clothes Washer
- Television

## Phase 4 — EPA-focused
- Range
- Cooktop
- Clothes Dryer
- Ventilating Hood
- Monitor
- Computer
- Tablet

## Phase 5 — History
New/open/resolved/reopened + population changes.

## Phase 6 — GitHub Actions operational hardening
Actions already runs from Phase 0. This phase hardens full-run orchestration, history retrieval, evidence retention, failure recovery, resource budgets, and scheduling.
Manual full run first; schedule only after stability.

## Phase 7 — GitHub Pages
Deploy validated site only.

---

# 24. GitHub Actions

Actions is the primary execution environment throughout implementation. Use the same versioned bootstrap for probe, CI, smoke, and full runs. Record runner image/version and installed dependency versions. A pinned OS label does not freeze the image contents.

## runner-probe.yml — Phase 0
- manual dispatch on standard `ubuntu-24.04` x64,
- explicit runtime and Playwright Chromium/system dependency installation,
- PyMuPDF direct-text extraction and RapidOCR image-only fallback,
- live Samsung/EPA access, JSON/PDF integrity, and browser-visible checks,
- per-check execution status, elapsed time, resource measurements,
- sanitized diagnostic artifact and job summary even after ordinary step failure.

## Hosted-runner execution contract
- Use workspace-relative paths and UTC timestamps; never depend on a personal PC path or interactive session.
- Use one acquisition/assessment/build job initially to preserve one canonical population/run. Introduce sharding only after measured resource limits, with explicit run/config/source-snapshot validation on merge.
- Stream documents, bound browser contexts, and persist stage outputs incrementally. Keep OCR worker/thread baseline conservative.
- Cache versioned dependencies/OCR model binaries only as an optimization. Cache miss must succeed. Current audit facts are not a dependency cache.
- Persist prior validated history explicitly; runners do not retain it between jobs. Missing or incompatible history must be visible, not silently treated as an empty history.
- Give collection jobs read-only repository permissions; grant deployment permissions only to the validated publication job.
- Bound request retries and job/stage timeouts. HTTP 403/429 is a hosted-source access/health failure, never proof of a missing product document or certification.
- Upload available failure diagnostics without masking the failed audit exit status. Hard cancellation/runner loss may prevent final uploads, so stage checkpoints must be small and frequent.
- Produce an immutable validated bundle plus manifest. Publication consumes that bundle without another crawl or assessment.
- Require a hosted Actions run URL, commit, run/attempt identifier, logs, and artifact manifest for every phase PASS.

See `US_SAMSUNG_REGULATORY_AUDIT_EXECUTION_GUIDE_v1.md` for initial resource budgets and phase gates.

## ci.yml
- install
- lint
- type check
- unit
- contract tests
- fixture dashboard build

No full live crawl.

## smoke-audit.yml
Manual, small live sample.

## full-audit.yml
Initially manual.

```text
discover
→ extract
→ labels
→ OCR
→ EPA
→ assess
→ consolidate
→ validate
→ dashboard
→ upload raw evidence artifact
```

## pages.yml
Deploy only validated `site/`.

---

# 25. Network policy

Initial baseline:

```text
HTTP concurrency: 2–3
timeout: 30 sec
retry: 3
backoff: exponential + jitter
```

403/429/site-structure changes are pipeline-health events, not mass compliance findings.

---

# 26. Tests

## Unit
- SKU normalization
- numeric normalization
- model matching
- OCR confusion candidates
- cross-field corroboration
- kWh matching
- EPA hierarchy
- issue priority
- history
- presentation mapping

## Contract
Fixture-backed:
- pf_search
- bridge_data
- EPA
- EnergyGuide parser

## OCR regression fixtures
Must include:
- embedded-text PDF
- image-only PDF
- low-resolution label
- B↔8
- O↔0
- I/l↔1
- S↔5
- wildcard
- repeated wildcard
- corrected OCR case
- true wrong-model case
- missing kWh
- malformed PDF

Assert:
- chosen engine
- raw extraction
- normalized result
- corrected/suspect state
- final issue code.

---

# 27. Acceptance gates

## Population
- rendered tiles reconcile
- PLP result count reconciles
- pf_search total reconciles
- exact-SKU duplicates explained
- no silent loss

## PDP
- structured parser works
- SKU identity verified
- contract drift surfaced

## EnergyGuide
- URL provenance known
- document valid
- extraction engine recorded
- required fields or explicit review/error

## OCR
- PyMuPDF always primary
- fallback reason logged
- engine reused
- thread baseline 1/1
- 2× baseline OCR
- 3× ROI+Otsu retry
- raw/corrected values both kept
- confusion correction prevents false mismatch

## EPA
- current source snapshot known
- family adapter validated
- ambiguity → review

## Publish
Every family must satisfy:

```text
population_valid
source_contract_valid
assessment_output_valid
counts_reconcile
run_id_consistent
```

Mixed generations = fail.

---

# 28. Public repository safety

Never commit:
- corporate credentials,
- internal tokens,
- internal CA certificates,
- proprietary internal documents,
- internal GitHub content,
- confidential internal URLs,
- personal data.

Large/raw captures stay in Actions artifacts.

---

# 29. Required documents

```text
PROJECT_CHARTER.md
MASTER_PLAN.md
SAMSUNG_SOURCE_CONTRACTS.md
EPA_SOURCE_CONTRACTS.md
OCR_CONTRACT.md
AUDIT_RULES.md
DATA_CONTRACTS.md
PIPELINE.md
TEST_STRATEGY.md
RUNBOOK.md
DECISIONS.md
```

---

# 30. First Codex session prompt

```text
Read AGENTS.md and docs/MASTER_PLAN.md completely.

This is a clean-room greenfield project.
Do not copy undocumented internal implementation code.

Work on Phase 0 only.

1. Create repository/documentation skeleton.
2. Inspect current Samsung US network behavior:
   - PLP pf_search endpoint/pagination
   - representative/sub SKU structure
   - PDP URL field
   - PDP bridge_data endpoint
   - model field
   - spec table structure
   - EnergyGuide PDF field
   - ENERGY STAR fields
3. Capture sanitized fixtures.
4. Identify current official EPA datasets for all configured families.
5. Verify GitHub-hosted Ubuntu access to:
   - Samsung PLP
   - pf_search
   - PDP
   - bridge_data
   - EnergyGuide PDF
   - EPA API
   - Playwright
6. Create source contract tests.
7. Do not implement compliance rules yet.
8. Report ambiguities and stop after Phase 0.
```

---

# 31. OCR Codex implementation prompt

```text
Implement OCR exactly according to docs/OCR_CONTRACT.md.

Hard requirements:
- PyMuPDF embedded/block text is always primary.
- RapidOCR is fallback only.
- Fallback is driven by explicit quality/required-field failures.
- Reuse one RapidOCR engine per run/worker.
- ONNX/OpenCV thread baseline = 1/1.
- Default render = 2×.
- Model/wildcard retry = 3× ROI + grayscale + Otsu.
- Preserve raw and corrected values separately.
- Handle B↔8, O↔0, I↔1, l↔1, S↔5 as contextual candidates.
- Never globally replace characters.
- Confusion-only differences may be corrected only with independent corroboration such as remaining model identity, kWh, capacity, and EPA values.
- Confident correction → ENERGYGUIDE_OCR_MODEL_CHAR_CORRECTED.
- Unresolved plausible confusion → ENERGYGUIDE_OCR_MODEL_CHAR_SUSPECT / MEDIUM.
- Genuine mismatch after reconciliation → wrong-model rule.
- Add regression fixtures for every confusion class and a real mismatch control.
```

---

# 32. Definition of Done — V1

V1 requires:

- 11 configured families
- pf_search population acquisition
- representative/sub-SKU provenance
- PLP validation gate
- bridge_data PDP acquisition
- PDP model validation
- PDP kWh extraction
- EnergyGuide URL extraction
- PDF integrity validation
- PyMuPDF primary extraction
- RapidOCR fallback
- optimized OCR retry
- OCR confusion reconciliation
- label model comparison
- label kWh comparison
- EPA certification lookup
- EPA model matching
- EPA kWh reconciliation where available
- ENERGY STAR claim consistency
- FTC/EPA domain separation
- existing HIGH/MEDIUM/LOW semantics
- pipeline health separated
- reproducible evidence
- raw evidence Actions artifact
- compact public evidence
- history
- deterministic full dashboard build
- CI
- live smoke workflow
- validated full audit workflow
- GitHub Pages
- zero stale mixed-run data
- zero silent pipeline failure
- no automated final legal conclusion

---

# 33. Final engineering principle

Audit trustworthiness is more important than producing a result.

When uncertain, emit:

```text
REVIEW_REQUIRED
PIPELINE_ERROR
NOT_EVALUATED
```

rather than false certainty.

OCR principle:

```text
recognition difference
≠ compliance mismatch
```

until the system has considered:
- known OCR confusion pairs,
- other model characters,
- PDP kWh,
- EnergyGuide kWh,
- EPA model/kWh where available,
- family-specific corroborating values.

Discovery principle:

```text
structured Samsung data first
browser observation second
guessing last
```

Presentation principle:

```text
canonical data first
derived presentation second
full static build last
```

Every dashboard conclusion must be traceable to captured source evidence and a versioned rule.
