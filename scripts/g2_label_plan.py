"""Plan bounded EnergyGuide observation from exact-SKU Support metadata only."""

from typing import Any
from urllib.parse import urlsplit


def declared_energyguide_documents(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Keep every Support-declared PDF candidate; choose no canonical document."""
    rows = []
    seen = set()
    for result in results:
        if result.get("status") != "VERIFIED_EXACT_IDENTITY":
            continue
        sku = result.get("exact_sku")
        facts = result.get("pdp_facts_raw")
        if not isinstance(sku, str) or not sku or not isinstance(facts, dict):
            raise ValueError("Verified PDP result lacks exact-SKU source facts")
        if facts.get("exact_sku") != sku or sku in seen:
            raise ValueError("EnergyGuide plan has mixed or duplicate exact SKU")
        seen.add(sku)
        documents = facts.get("energyguide_documents")
        if not isinstance(documents, list):
            raise ValueError("Support EnergyGuide document collection is invalid")
        if not documents:
            rows.append({"exact_sku": sku, "document_status": "NOT_OBSERVED", "documents": []})
            continue
        planned = []
        for index, document in enumerate(documents):
            if not isinstance(document, dict) or not isinstance(document.get("url"), str):
                raise ValueError("Support EnergyGuide document URL is invalid")
            parts = urlsplit(document["url"])
            if parts.scheme != "https" or not parts.netloc:
                raise ValueError("Support EnergyGuide document URL must be HTTPS")
            planned.append(
                {
                    "source_document_index": index,
                    "name_raw": document.get("name"),
                    "type_raw": document.get("type"),
                    "url": document["url"],
                    "field_selection": "NOT_EVALUATED",
                    "identity_matching": "NOT_EVALUATED",
                }
            )
        rows.append({"exact_sku": sku, "document_status": "DECLARED_BY_EXACT_SUPPORT", "documents": planned})
    return {
        "scope": "Support-declared EnergyGuide document planning only; no PDF retrieval or field selection",
        "rows": rows,
        "selected_document_count": sum(len(row["documents"]) for row in rows),
        "canonical_document_selection": "NOT_EVALUATED",
    }
