# G1 draft data contracts

Status: technical draft, not an approved audit or aggregation policy. `draft-1`
is deliberately not a stable production schema. G1 is RUNNING, not accepted.
The contract implementation is `src/regaudit/contracts.py`; fixtures are synthetic.

The envelope contains one RunManifest plus products, evidence, facts and
assessments. RunManifest records immutable code/config identity, UTC-aware
timestamps, source contract and actual Python version. Rules remain disabled,
rule_version is null and no CLI command runs collectors or assessments.
An empty init-run skeleton is OUTPUT_MISSING, never execution SUCCESS.
UUID run identifiers avoid reuse; output creation fails rather than overwrites.

Proposed product identity is `(run_id, exact_sku)` without case conversion,
wildcard expansion or fuzzy matching. A product keeps an array of listing
provenance including product_group, source_family_id, representative SKU/role,
PLP/PDP URL and raw pf_search hash. A washer/dryer combo retains both groups.
Duplicate product records are rejected rather than silently merged. This draft
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

FactRecord is a generic draft transport with PDP/ENERGYGUIDE/EPA kind and named
observations. It does not yet implement the MASTER_PLAN's specialized
PdpFactRecord, EnergyGuideExtractionRecord and EpaRecord field/unit contracts.
Those are remaining G1 work before any normalization or comparison engine.

AssessmentRecord preserves individual FTC/EPA records and same-product evidence
links. The CLI accepts only NOT_EVALUATED with null rule/issue/severity.
The Python validator's synthetic_assessments option is fixture-only: a test
preserves one synthetic SKU with two existing issue codes across FTC/EPA.
There is no CLI switch enabling synthetic findings or real audit conclusions.
The fixture's one-product/two-record assertion tests transport cardinality;
it does not implement or approve D02/D04's report counting/priority policy.

Five `.yaml` configs use JSON syntax, a YAML 1.2 subset, parsed with the standard
library only. Canonical JSON of all five contributes to config_hash. Source
routes are copied from G0 observations, not eligibility rules. Assessment and
presentation enablement are rejected by the CLI. Rich config schema validation
remains G1 work. No model, API key, browser or third-party package is needed.

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
