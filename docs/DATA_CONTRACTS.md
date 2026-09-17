# G1 draft data contracts

Status: technical draft with approved G1 identity/count/ID baseline; assessment
policies remain disabled. See G1_DECISION_PROPOSAL.md. `draft-1`
is deliberately not a stable production schema. G1 is RUNNING, not accepted.
The contract implementation is `src/regaudit/contracts.py`; fixtures are synthetic.

The envelope contains one RunManifest plus products, evidence, facts and
assessments. RunManifest records immutable code/config identity, UTC-aware
timestamps, source contract and actual Python version. Rules remain disabled,
rule_version is null and no CLI command runs collectors or assessments.
An empty init-run skeleton is OUTPUT_MISSING, never execution SUCCESS.
UUID run identifiers avoid reuse; output creation fails rather than overwrites.

Approved product identity is `(run_id, exact_sku)` without case conversion,
wildcard expansion or fuzzy matching. A product keeps an array of listing
provenance including product_group, source_family_id, representative SKU/role,
PLP/PDP URL and raw pf_search hash. Each listing also carries observations for
source family code, commerce status, stock/ecom flags and variant attributes;
source flag encodings are retained without conversion. A washer/dryer combo
retains both groups.
population.canonicalize_products explicitly merges repeated exact SKU records
and retains every distinct listing observation, including conflicting values.
The final bundle rejects duplicates rather than silently deduplicating. This draft
does not infer certification identity or define report coverage denominators.

Evidence carries run/group/SKU, source URL/time, raw SHA256, parser identity,
evidence type and relative path. Every referenced evidence ID must exist and
belong to the same run/group/SKU. CLI validation requires an evidence root and
checks actual file hashes, missing files, path traversal and escaping symlinks.
Hash checks do not prove completeness, freshness or regulatory applicability.

Observation state is VALUE, MISSING, NOT_OBSERVED, NOT_APPLICABLE or ERROR.
VALUE preserves numeric zero and boolean false; null is not an observed value.
Absent states require null value/error; ERROR requires null value and an error.
NaN is rejected. Source errors cannot produce execution SUCCESS or evaluated
assessments in this draft. This conservative boundary is not D10's final rule.

FactRecord retains common run/group/SKU/evidence identity. Its observations now
require the exact fields of PdpFactRecord, EnergyGuideExtractionRecord or EpaRecord
in src/regaudit/facts.py. Required fields may explicitly be NOT_OBSERVED rather
than omitted. The draft evolves in place; previously generic fixture fields are
no longer accepted. No stable production bundles have been emitted.

| Kind | Required source observation fields | Typed boundaries |
|---|---|---|
| PDP | model, URL/title, annual energy/capacity, label URL, three independent claim channels, bridge hash | Boolean claims reject strings/numbers; hash belongs to referenced raw evidence |
| EnergyGuide | document URL/hash/status, extraction engine, embedded/OCR text, raw/normalized model, energy/capacity, confusion flags/reasons, fallback reason, OCR scale/ROI | Raw OCR text may be empty; scale finite/positive; ROI records zero-based page, increasing box extents and coordinate unit |
| EPA | dataset/row identity, model, UPC, annual energy, markets, certification source status, retrieval time/hash | Markets remain source string arrays; timestamps require timezone; missing UPC never infers failed certification |

Annual-energy VALUE is `{amount, unit, raw}` with finite numeric amount (zero
allowed, boolean rejected), unit `kWh/year` and nonempty raw source text.
Capacity uses the same envelope while retaining its explicit source unit. No
conversion or physical-range rule is applied. Ambiguous or unparsed measures
remain NOT_OBSERVED/ERROR; source raw files are preserved separately.
Source status strings are retained without interpreting active/certified status.
Raw and normalized models are separate observations; validation runs no OCR
correction or model matching. Synthetic typed-bundle.json exercises all kinds
without claiming actual document readability or regulatory applicability.

AssessmentRecord preserves individual FTC/EPA records and same-product evidence
links. The CLI accepts only NOT_EVALUATED with null rule/issue/severity.
The Python validator's synthetic_assessments option is fixture-only: a test
preserves one synthetic SKU with two existing issue codes across FTC/EPA.
There is no CLI switch enabling synthetic findings or real audit conclusions.
The fixture's one-product/two-record assertion tests transport cardinality;
report.py now implements approved finding/affected-SKU counting without any
representative severity or priority policy. One SKU row retains all assessments.
Zero recorded findings with assessment_enabled=false means unevaluated, not
compliance PASS. The summarize CLI requires raw hashes and refuses evaluated
findings until the assessment engine is authorized/implemented in G2.

Five `.yaml` configs use JSON syntax, a YAML 1.2 subset, parsed with the standard
library only. Canonical JSON of all five contributes to config_hash. Source
routes are copied from G0 observations, not eligibility rules. Assessment and
presentation enablement are rejected by the CLI. Strict config validation now
rejects missing/unknown fields, duplicate source legs, missing product groups,
malformed dataset IDs, runtime lock mismatches and silent decision closure.
Source metadata changes alter config_hash; formatting alone does not.
No model, API key, browser or third-party package is needed.

Run locally from repository root:

```sh
PYTHONPATH=src python -m regaudit.cli init-run --git-sha "$(git rev-parse HEAD)" --output runtime/draft/run.json
PYTHONPATH=src python -m regaudit.cli validate fixtures/g1/bundle.json --evidence-root fixtures/g1
python checks/g1/run.py
```

The last command requires zero skipped tests to report PASS. On Windows without
symlink privileges its Linux security case may skip and the report fails;
hosted ubuntu-24.04 must execute every case. Actions CI separately checks Python
3.11 compatibility and the audit runtime 3.12.14. Its PASS is limited to these
draft fixtures, not the G1 acceptance gate or full G0 source suite.
Setuptools packaging is a conventional optional build path; CI directly uses
the source tree and downloads no Python packages. Packaging is not yet verified.

Artifacts use the existing 14-day review window. This is not approval of durable
storage, long-term raw retention or D12's future retry/recovery policy.
