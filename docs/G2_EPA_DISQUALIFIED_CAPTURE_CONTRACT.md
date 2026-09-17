# EPA disqualified-list raw capture contract

## What this step does

The manual GitHub Actions workflow first downloads EPA's official Integrity
page. It finds the single link that EPA labels as its disqualified-products
XLSX, downloads that file, and stores both responses as an artifact. The
manifest records requested and final URLs, HTTP status, content type, byte size,
SHA-256 and capture time. A replay immediately verifies the saved bytes, the
discovered link and the XLSX ZIP container signature.

This is analogous to photographing a source document, dating it, and checking
that the stored photograph has not changed. It does not open the spreadsheet to
read rows.

## Explicit boundaries

- No XLSX worksheet, cell, model number or product category is parsed.
- No Samsung model is compared with this list.
- No missing result means "not disqualified".
- No present result means a product finding, because identity and scope have not
  been defined.
- `identity_matching`, `disqualification_state` and `assessment` remain
  `NOT_EVALUATED` in every successful capture manifest.

A failed download, ambiguous link, non-XLSX response or changed replayed bytes
fails the capture. It cannot produce a positive observation.

## How it is run and verified

Run **G2 EPA disqualified-list capture** manually on standard
`ubuntu-24.04`. The workflow uploads the raw artifacts even after a failure, so
the response can be reviewed. The inexpensive **G2 offline source contracts**
workflow tests the link-discovery, container and replay failure paths on Python
3.11 and 3.12. Documentation-only changes do not trigger live collection.

The source page is [EPA Integrity Efforts](https://www.energystar.gov/partner-resources/products_partner_resources/products_integrity),
which links EPA's disqualified-products XLSX. The next potential stage would be
an isolated spreadsheet schema review. It needs a separate decision before any
row parser, identifier comparison or audit consequence is implemented.

Recommended model: Terra medium for the capture/replay integration. Luna low is
enough for later documentation-only maintenance; use Sol medium only when
deciding source meaning or a matching rule.
