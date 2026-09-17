# Phase 1 / G1 acceptance record

Status: PASS — accepted 2026-09-17 after downloaded hosted reports/wheels and
SHA256 verification. Final corrected run: 35172241517, code
dccaba94537ba66372eb1f3009af7d776eafded6, attempt 1. Both ubuntu-24.04 x64 jobs
(Python 3.11.16 and 3.12.14) executed 80 fixture tests with zero skips/errors/
failures and passed all 15 quality/installed-CLI checks. Jobs 105046180101 /
105046179932. Immutable report/wheel/ZIP hashes, tool versions and artifact expiry
are archived in docs/evidence/g1-acceptance-recon.json.
Scope: schemas, disabled configs, run/evidence manifests, offline CLI, product
identity/report counts, fixtures and quality CI. G0 prerequisite is accepted in
G0_ACCEPTANCE_RECORD.md. G1 is not a product compliance or live collection PASS.

| Required G1 category | Concrete verification |
|---|---|
| Typed baseline records | G1_FIELD_INVENTORY.md maps every MASTER_PLAN record field; exact-key validators cover PDP/EnergyGuide/EPA and common identities |
| Observation distinctions | Zero/false remain observed; null is not a value; missing/unobserved/N/A/error remain distinct; source errors cannot yield execution SUCCESS |
| Independent claims | PLP, structured PDP, spec PDP flags preserved independently; integer/string flags rejected at the typed boolean boundary |
| Canonical population | Same exact SKU merges listing provenance explicitly; distinct variants/case/wildcards retained; cross-run merge rejected; conflicting source flags retained |
| Multiple assessments/counts | FTC HIGH plus EPA MEDIUM fixture yields one SKU row, two findings, one affected SKU; both assessments and evidence references preserved |
| Group overlap | Washer/dryer membership and attributed group findings can overlap; global counts are computed directly, never by summing overlapping subtotals |
| Evidence graph/storage | Run/group/SKU references checked; missing/corrupt stored evidence rejected; traversal and escaping symlinks rejected, mandatory on hosted Linux |
| Config integrity | Five exact-key configs; code/config/source identities, runtime lock, full product-group coverage, duplicate routes and disabled policy boundaries checked |
| Run identity and serialization | UUID uniqueness, exclusive output creation, round-trip JSON, timezone-aware timestamps and SHA fields checked |
| Static quality | Pinned Ruff E4/E7/E9/F + format; Mypy checks all 7 package files and requires complete function annotations; dynamic JSON boundaries remain Any, not full strict mode |
| Installed CLI | Wheel built with pinned backend, installed offline in fresh venv, imported only from installed environment; entrypoint exercised outside repository without PYTHONPATH |
| Hosted execution | Final same-code matrix must pass both fixture and quality reports on ubuntu-24.04 x64, Python 3.11 and 3.12.14, without skipped fixture cases |

User authorization on 2026-09-17 resolved the G1 baseline portions of
D02/D04/D08/D11/D12, detailed in G1_DECISION_PROPOSAL.md. No further confirmation
of those criteria is required. Partial approval does not resolve every portion
of these decisions. Each report records its run/code identity and hashes.

G2 remains NOT_STARTED. Its assessed bundle/rule engine and source adapters must
be versioned before evaluated production findings are accepted. Energy
tolerance/test basis, independent OCR corroboration and correction, active/US
certification and wildcard identity, issue priority/severity summary, full
population completeness/coverage and collection-error boundaries stay open for
G2/G4. Durable raw retention/restoration and publication stay at G5–G7.
The 14-day review artifacts and synthetic finding fixtures approve neither
regulatory applicability nor long-term evidence storage.

Failure history: initial run 35172198096 at b931212 failed workflow YAML parsing
before jobs ran. The pip command containing a colon was converted to a YAML block
at dccaba9; the final acceptance must reference the successful corrected run.

G1 does not replay G0's installed OCR/source suite in its fixture jobs. It relies
on the recorded G0 prerequisite and tests only phase-1 additions. Audit execution
has no LLM calls and no third-party runtime dependencies; pinned PyPI tooling is
used for development CI only. This record makes no assertion that all live SKUs
have PDP/label/EPA data or have been assessed.

The broad existing requirements-lock triggers also replayed G0 runtime freeze/
recovery 35172199156, runner probe 35172199151 and product source contracts
35172199094 at b931212. All three run conclusions were API-verified success;
these incidental runs are not substituted for the corrected final G1 reports.
