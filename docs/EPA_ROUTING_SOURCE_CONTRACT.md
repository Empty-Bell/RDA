# Official EPA source-routing reconnaissance

Phase 0 only. Bounded hosted extraction PASS in
[run 35168707877](https://github.com/Empty-Bell/RDA/actions/runs/35168707877), commit
cfac061e4cb81314b031c60b1febbe905b6c75cd, attempt 1, job 105035493022.
G0 and compliance NOT_EVALUATED. Official references observed 2026-09-17.

## Active-source advertisement

The [EPA official DCAT feed](https://data.energystar.gov/data.json) advertises all
nine configured main datasets and `8wj2-sec8` (Model Index) under
`Active Specifications`. This is stronger source-category evidence than a catalog
keyword match, but does not prove exclusive active version, every model's current
US certification or source completeness across every program. The Model Index
description presents it as a simplified current-model list; it supplies basic
identity fields rather than replacing per-category efficiency data. The
[EPA tools page](https://www.energystar.gov/products/productstr) links its non-lighting
list to this index and describes daily updates. Update timestamps alone are not
withdrawal/expiry rules.

The [official specification index](https://www.energystar.gov/products/spec) lists:

| Product | Observed In Effect version | Main configured source |
|---|---|---|
| Consumer Refrigeration | 5.1 | p5st-her9 |
| Dishwashers | 7.0 | q8py-6w3f |
| Clothes Washers | 8.1 | bghd-e2wd |
| Televisions | 9.1 | pd96-rr3d |
| Residential Electric Cooking Products | 1.0 | m6gi-ng33 |
| Clothes Dryers | 1.1 | t9u7-4d2j |
| Fans, Ventilating | 4.2 | 8dv7-nngq |
| Displays | 8.0 | qbg3-d468 |
| Computers | 9.0 | rxdj-2c88 |

These version observations are dated source facts, not automatic matching policies.
The probe retains actual table cells, official PDF links and effective dates;
missing/duplicate rows, nonofficial links and status/version format drift fail.
EPA documents a dataset deprecation/replacement process in
[API User Essentials](https://www.energystar.gov/products/spec/energy_star_api_user_essentials_pd).

## Alternate combo view

[`9jai-gs6t` official metadata](https://data.energystar.gov/api/views/9jai-gs6t.json)
describes a Combination All-in-One Washer/Dryer-only view of products under the
Clothes Washers 8.0/8.1 specification, referencing the source dataset for other
types. Public flags include `calculatedView` and `soqlBasedView`; `parentViewId`
is null. These flags and descriptive provenance do not prove a machine-readable
parent relationship. The view is not observed as a separate entry in the DCAT
feed. That omission is not retirement or nonapplicability evidence.

The schema retains washer annual energy and separately named estimated dryer
annual energy, dryer capacity, heat-pump and CEF fields. Do not collapse the two
energy components or reinterpret a washer label as combined appliance energy.
The probe compares identity multisets `(pd_id, brand_name, model_number)` for:
- the declared literal Samsung query in `9jai-gs6t`, and
- the literal Samsung + `special_type = 'Combination All-in-One Washer/Dryer'`
  query in `bghd-e2wd`.

Both scans require terminal pagination, before/after count and metadata stability,
unique system row IDs and identity fields, reusing established query boundaries.
Equality is an observed cohort relation; it does not approve a canonical join,
row deduplication, wildcard expansion or stacked/laundry-center routing. No change
is made to production FAMILIES or the established nine-dataset adapter contracts.

## Program scope evidence; individual applicability remains open

- [Ventilating Fans 4.2, §2, PDF pages 4–5](https://www.energystar.gov/sites/default/files/ENERGY%20STAR%20Ventilating%20Fans%20Specification%20Version%204.2.pdf)
  includes residential range hoods and excludes commercial cooking range hoods
  among other types. `8dv7-nngq` is additionally probed for actual `Range Hood`
  type rows across brands. A literal Samsung-brand scan with zero rows never
  establishes hood N/A or an individual model's certification absence.
- [Electric Cooking 1.0, §2, PDF page 5](https://www.energystar.gov/sites/default/files/2024-08/ENERGY%20STAR%20Residential%20Electric%20Cooking%20Products%20V1.0%20Final%20Specification%20Rev.%20October%20-%202023.pdf)
  includes conventional electric cooking tops and the cooking-top component of
  electric ranges; gas cooking tops/ranges/standalone ovens and electric standalone
  ovens are excluded under this specification. Mixed/dual-fuel and SKU-level
  product definitions still require source facts and an approved D09 policy.
- [Computers 9.0, §§1–2, PDF pages 6 and 10–11](https://www.energystar.gov/sites/default/files/2025-04/ENERGY%20STAR%20Computers%20Version%209.0%20Final%20Specification.pdf)
  covers Notebook and Slate/Tablet definitions; cellular voice capability is one
  listed exclusion. A retail Tablet label or operating-system name alone is not
  a sufficient applicability decision. Wi-Fi/LTE/voice/configuration variants
  must retain their source facts.

## Verification and cost

`epa-routing-recon.yml` uses pinned Node24 Actions and Python 3.12.14 on standard
ubuntu-24.04 x64. It installs no packages and uses no browser/OCR/LLM. Dedicated
source-backed sanitized fixtures live in `fixtures/epa-routing`; their contract
tests run separately from the expensive Samsung browser suite. Existing twelve
EPA query-boundary tests also run. Fetches have 30-second timeouts, an 8 MiB body
bound and a 5000-row diagnostic scan bound; incomplete/error responses fail.

Raw public query bytes precede decoding; metadata/DCAT/HTML keep response hashes
and public projections, omitting contacts, account identifiers and analytics.
Always-upload diagnostic reports remain FAIL on errors. Source identity/schema
and combo energy-component field drift are rejected. Artifact retention is 14 days.
Sanitized fixture manifests use committed LF byte hashes and the G0 checker also
accepts the new restricted fixture directory. This validates extraction only.

## Hosted observations

Sixteen dedicated routing tests and twelve existing query-boundary tests passed.
The official DCAT feed has 54 projected entries; all nine main configured sources
and the Model Index are advertised Active Specifications. The spec table provides
all nine required In Effect rows and official version/effective-date PDF links.
This is official advertisement/status evidence, not exclusive-version proof.

The combo and parent-filtered Samsung scans each have three rows, with observed
stable metadata/counts, terminal pages and equal identity multisets. Raw model
patterns are WD53DBA9**H*, WD80H53*H* and WD90F53*V*. Their washer annual-energy
field is 103 kWh; their separately named estimated dryer annual-energy field is
319, 319 and 608 kWh respectively. These are raw EPA quantities, not an approved
retail SKU match or comparison to EnergyGuide. Preserve wildcard counts.

The fan dataset's actual type field is `unit_type`. The cross-brand type probe
returned three Air King Range Hood rows. This confirms that this source contains
hood records; it does not establish a Samsung candidate or all hood applicability.
The first probe incorrectly used generic `product_type` and received HTTP 400.
A second run reached combo paging but failed because SoQL star selections must
start the select list. Explicit observed metadata fields now replace `*`; raw
failures and corrections are retained in epa-routing-failure-history.json.

Actual metadata/table/catalog/cohort/hood projections and response/ZIP/report hashes
are in docs/evidence/epa-routing-recon.json. No production source route was changed.
The separate [fixture integrity run](https://github.com/Empty-Bell/RDA/actions/runs/35168643898)
checks the four routing fixtures with existing repository fixtures independently
of this source extraction gate.

Next closure work: official FTC/EPA family applicability evidence table, stacked/
laundry-center and per-configuration observations, then explicit G0 review. D09
and all existing semantic decisions remain OPEN; no compliance finding is emitted.
