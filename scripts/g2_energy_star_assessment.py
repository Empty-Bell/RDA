"""Apply the approved three-point Energy Star rule to complete source inputs."""

REGISTERED_STATES = {
    "MATCHED_RAW_LITERAL_CANDIDATES",
    "MATCHED_APPROVED_NORMALIZED_LITERAL_CANDIDATES",
    "MATCHED_CURRENT_INDEX_POSITIONAL_PATTERN_CANDIDATES",
}
UNREGISTERED_STATE = "COMPLETE_NO_LITERAL_OR_PATTERN_CANDIDATE"
LOW_ISSUE = "SAMSUNG_ENERGY_STAR_SOURCE_CONFLICT"
HIGH_ISSUE = "CRITICAL_ENERGY_STAR_ELIGIBILITY_CANDIDATE"


def _flag_point(value: object) -> dict:
    state = {"Y": "PRESENT", "N": "ABSENT"}.get(value, "UNKNOWN")
    return {"state": state, "raw_value": value}


def _spec_point(raw_rows: object, evidence: dict | None) -> dict:
    if not isinstance(raw_rows, list) or not isinstance(evidence, dict):
        return {"state": "UNKNOWN", "raw_rows": raw_rows}
    if evidence.get("full_specs_collection") != "COMPLETE_EXACT_SKU_SPECS":
        return {"state": "UNKNOWN", "raw_rows": raw_rows}
    certification_rows = [
        row for row in raw_rows
        if isinstance(row, dict)
        and "energy star" in str(row.get("name", "")).lower()
        and "certif" in str(row.get("name", "")).lower()
    ]
    if not certification_rows:
        return {"state": "ABSENT", "raw_rows": raw_rows}
    values = [str(row.get("value", "")).strip().lower() for row in certification_rows]
    positive = {"yes", "y", "true"}
    negative = {"no", "n", "false"}
    if all(value in positive for value in values):
        return {"state": "PRESENT", "raw_rows": raw_rows}
    if all(value in negative for value in values):
        return {"state": "ABSENT", "raw_rows": raw_rows}
    return {"state": "UNKNOWN", "raw_rows": raw_rows}


def _epa_registration(candidate: dict) -> dict:
    state = candidate.get("candidate_projection_state")
    if state in REGISTERED_STATES:
        rows = (
            candidate.get("raw_literal_candidates", [])
            + candidate.get("approved_normalized_literal_candidates", [])
            + candidate.get("current_index_pattern_candidates", [])
        )
        return {"state": "PRESENT", "candidate_projection_state": state, "candidates": rows}
    if state == UNREGISTERED_STATE:
        return {"state": "ABSENT", "candidate_projection_state": state, "candidates": []}
    return {
        "state": "UNKNOWN",
        "candidate_projection_state": state,
        "candidates": candidate.get("unsupported_pattern_references", []),
    }


def _decide(registration: str, points: dict) -> tuple[str, str | None, str | None]:
    states = [point["state"] for point in points.values()]
    if registration == "PRESENT":
        if all(state == "PRESENT" for state in states):
            return "PASS", None, None
        if "ABSENT" in states:
            return "LOW", "LOW", LOW_ISSUE
        return "NOT_EVALUATED", None, None
    if registration == "ABSENT":
        if "PRESENT" in states:
            return "HIGH", "HIGH", HIGH_ISSUE
        if all(state == "ABSENT" for state in states):
            return "NO_FINDING", None, None
    return "NOT_EVALUATED", None, None


def build_assessment(
    review: dict,
    *,
    expected_exact_skus: int,
    query_completeness: str,
) -> dict:
    """Evaluate each exact SKU after validating complete same-run input sets."""
    if review.get("contract") != "G2_ENERGY_STAR_THREE_POINT_INPUT_REVIEW_ONLY_V1":
        raise ValueError("Energy Star input review contract unavailable")
    records = review.get("records")
    if not isinstance(records, list) or len(records) != expected_exact_skus:
        raise ValueError("Energy Star source point coverage is incomplete")
    if len({record.get("exact_sku") for record in records}) != len(records):
        raise ValueError("Energy Star source point exact SKU duplicated")
    if query_completeness != "COMPLETE_OBSERVED_QUERY":
        raise ValueError("EPA Current Model Index query is incomplete")
    if review.get("current_index_query_completeness") != query_completeness:
        raise ValueError("Energy Star inputs and Current Model Index completeness differ")
    if not review.get("source_run_id"):
        raise ValueError("Energy Star source run provenance missing")

    output = []
    for record in sorted(records, key=lambda item: item["exact_sku"]):
        source_refs = record.get("source_evidence_refs") or {}
        plp_ref = source_refs.get("plp_logo_source")
        pdp_ref = source_refs.get("pdp_logo_source")
        spec_ref = source_refs.get("pdp_spec_certification_source")
        points = {
            "plp_logo": _flag_point(record["plp_logo_source"].get("raw_value")),
            "pdp_logo": _flag_point(record["pdp_logo_source"].get("raw_value")),
            "spec_certification": _spec_point(
                record["pdp_spec_certification_source"].get("raw_rows"), spec_ref
            ),
        }
        if plp_ref is None:
            points["plp_logo"]["state"] = "UNKNOWN"
        if pdp_ref is None:
            points["pdp_logo"]["state"] = "UNKNOWN"
        if spec_ref is None:
            points["spec_certification"]["state"] = "UNKNOWN"
        registration = _epa_registration(record["epa_current_index_candidate"])
        outcome, severity, issue_code = _decide(registration["state"], points)
        output.append({
            "exact_sku": record["exact_sku"],
            "epa_current_index_registration": registration,
            "publication_points": points,
            "publication_evidence_refs": source_refs,
            "outcome": outcome,
            "severity": severity,
            "issue_code": issue_code,
            "current_certification_state": (
                "OBSERVED_REGISTERED" if registration["state"] == "PRESENT"
                else "OBSERVED_NOT_REGISTERED" if registration["state"] == "ABSENT"
                else "NOT_EVALUATED"
            ),
        })
    counts = {}
    for record in output:
        counts[record["outcome"]] = counts.get(record["outcome"], 0) + 1
    return {
        "contract": "G2_ENERGY_STAR_THREE_POINT_ASSESSMENT_V1",
        "source_run_id": review["source_run_id"],
        "source_scope": "Exact-SKU Samsung declarations and complete same-run Current Model Index only",
        "source_observation_method": (
            "PLP PF energyStarFlg, PDP Next energyStarFlag, exact-SKU Bridge Specs "
            "certification rows and Current Model Index patterns"
        ),
        "decision_rule": {
            "registered_all_three_present": "PASS",
            "registered_any_confirmed_absent": {"outcome": "LOW", "issue_code": LOW_ISSUE},
            "unregistered_any_present": {"outcome": "HIGH", "issue_code": HIGH_ISSUE},
            "unregistered_all_absent": "NO_FINDING",
            "unknown_or_incomplete_inputs": "NOT_EVALUATED",
        },
        "coverage": {"expected_exact_skus": expected_exact_skus, "evaluated_records": len(output)},
        "overall_product_compliance": "NOT_EVALUATED",
        "counts": dict(sorted(counts.items())),
        "records": output,
    }
