# EPA wildcard and independent identity reconnaissance

Research date: 2026-09-17. Status: bounded hosted source-capture checkpoint PASS.
D07/D09 remain OPEN.
No matching, OCR correction or assessment is enabled.

## Official evidence and scope

| Source | Observed guidance | Boundary |
|---|---|---|
| [EPA UPC submission FAQ](https://www.energystar.gov/partner-resources/products_partner_resources/brand-owner/certifying-products/upc/faqs), questions 1–5, 9, 13–14 | One wildcard corresponds to one position; `#` requires a number. Extra/missing positions prevent that system's match. UPCs can associate with several specification versions or certification bodies. Leading zeros are retained. Bracket/pipe expressions are unsupported there. | Guidance for EPA's UPC submission system; not proof of Samsung EnergyGuide grammar. |
| [QPX XML documentation v2.9](https://www.energystar.gov/sites/default/files/2024-04/XML_Submission_System_Technical_Documentation_0.pdf), printed pp. 10–11, 27 | Submission guidance distinguishes `*` for letters and `#` for digits; version history records single-position clarification. Additional model identifiers are separate entries tied to the performance record. Bracket/pipe notation is discussed in submission guidance. | Submission grammar and UPC system capability are distinct. Retrieved v2.9 is dated 2024-02-07; this research does not prove it is the only current document. |
| [Residential refrigerator export](https://data.energystar.gov/api/views/p5st-her9/rows.pdf) | Indexed official export description says stars may denote A–Z or 0–9 feature variations without affecting energy performance. | Indexed description differs from QPX letter-only wording. Export body/metadata must be captured and verified on the hosted runner before adopting a character class. |
| [Consumer refrigeration submission template](https://www.energystar.gov/products/webservices/spec/67) | Currently-available-on-market and sold-in-market fields are separate; template scope names specifications 5.0/5.1. | Availability and dates alone are not certification currency. Template scope is not proof of the current public dataset's full schema. |

The width evidence supports investigating a fixed-position grammar. It does not
support variable-length shell glob matching. The alphabet evidence needs a
dataset-scoped resolution; no universal wildcard rule is proposed for approval.
The FAQ's space removal is also specific to that system. This project continues
to preserve spaces/case/suffixes and requires explicit approval before normalization.

## Independent EPA observation example

[EPA Product Finder record 2839420](https://www.energystar.gov/productfinder/product/certified-residential-refrigerators/details/2839420)
displays Samsung `RF23D*9600**`, annual energy 634 kWh/yr, volume 22.8 ft3,
United States and Canada markets, and a Certified Yes field. It lists UPCs
887276826820, 887276826837, 887276826844 and 887276826905.

These are EPA source observations independent of the label's OCR process.
They do not prove that exact Samsung SKU `RF23DB9600QLAA` is covered: the full
SKU has additional positions relative to the displayed pattern. A suffix or
exact additional-model mapping needs its own source-backed contract. Numeric
agreement must not choose the identity candidate and then corroborate that choice.

The record's current-looking page and Certified Yes field are useful provenance,
but this research does not establish the public API's current/withdrawn coverage,
specification version or complete query semantics. Preserve the PD_ID and all
candidate records instead of selecting the first or latest certification date.

## Unresolved evidence

- Samsung-specific EnergyGuide wildcard width, permitted characters and US suffix
  mapping were not established by the bounded official-domain searches. A label
  attached to an exact-SKU Support page is retrieval provenance, not a declared
  model-pattern grammar.
- Public dataset wildcard descriptions and their effective scope must be captured.
  The browser reader could not open the metadata API URL in this research; that
  tool error is not evidence of dataset absence or an HTTP source failure.
- Exact product UPC evidence from a verified Samsung PDP is needed before an EPA
  UPC association can be tested. Missing UPC remains unknown. UPC association may
  return multiple records and is not itself a current-certification decision.
- Supported additional-model structures, US market tokens, specification versions,
  withdrawn/disqualified handling and complete-query gates still require contracts.

## Next bounded work: source capture, no matcher

The separate hosted source-recon job passed as run 35189522017 at `ae632c7` on
ubuntu-24.04. Artifact 10483337728 has ZIP digest
`6293ab90b6ac297e3bc457477476ddb4ce0b8abb7774ae34cc1ed60678859926`.
It retained raw FAQ, QPX PDF, template, Product Finder record and dataset metadata
responses; each manifest SHA-256 replayed against its stored bytes. The successful
capture is evidence preservation only, not a grammar or matching acceptance.

The source-recon job uses locked Python
dependencies. Preserve raw response bytes before extracting a compact projection.
Capture the FAQ, QPX PDF, refrigerator metadata, and record 2839420; record URL,
UTC capture time, status, response hash and extraction version. A failed request
fails the job and retains diagnostics; it cannot yield an absent certification.
Do not download the huge full dataset PDF as a routine default. Inspect metadata
and bounded official records first; keep export-description provenance separate.

Hosted artifact verification must replay every projected claim against stored
bytes/hashes. Tests should cover malformed metadata, changed bytes, multiple
PD_IDs, preserved UPC leading zeros, market values, and unsupported syntax.
This source capture does not enable any grammar or identity conclusion.

Recommended model for the next evidence review/policy proposal: Sol medium.
Use Luna low for checkpoint documentation and fixture-only follow-up.
