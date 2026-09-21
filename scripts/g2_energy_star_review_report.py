"""Render a compact reviewer report from an assessed Energy Star artifact."""


def _markdown_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def render_review_report(assessment: dict) -> str:
    """Render findings and review clusters; never recompute a verdict."""
    if assessment.get("contract") != "G2_ENERGY_STAR_THREE_POINT_ASSESSMENT_V1":
        raise ValueError("Energy Star assessment contract unavailable")
    coverage = assessment.get("coverage") or {}
    counts = assessment.get("counts") or {}
    display_pass = counts.get("PASS", 0) + counts.get("NO_FINDING", 0)
    lines = [
        "# Refrigerator ENERGY STAR review report",
        "",
        f"Source run: `{assessment.get('source_run_id')}`",
        "",
        "This report presents the assessed artifact. It does not recompute certification, "
        "make a legal conclusion, or alter any exact-SKU finding.",
        "",
        "## Final UI summary",
        "",
        "PASS includes source-rule PASS and NO_FINDING outcomes. Raw outcomes remain in "
        "`energy-star-assessment.json` for audit traceability.",
        "",
        "| Expected exact SKUs | Evaluated | PASS | LOW | HIGH | Not evaluated |",
        "|---:|---:|---:|---:|---:|---:|",
        "| {expected} | {evaluated} | {display_pass} | {low} | {high} | {not_evaluated} |".format(
            expected=coverage.get("expected_exact_skus", 0),
            evaluated=coverage.get("evaluated_records", 0),
            display_pass=display_pass,
            low=counts.get("LOW", 0),
            high=counts.get("HIGH", 0),
            not_evaluated=counts.get("NOT_EVALUATED", 0),
        ),
        "",
        "## HIGH review clusters",
        "",
        "Each SKU below remains an independent HIGH finding. Clustering only reduces review repetition.",
        "",
        "| Samsung source family | Representative SKU | Exact SKU count | Exact SKUs |",
        "|---|---|---:|---|",
    ]
    clusters = (assessment.get("review_clusters") or {}).get("HIGH") or []
    for cluster in clusters:
        lines.append(
            "| {family} | {representative} | {count} | {skus} |".format(
                family=_markdown_cell(cluster.get("source_family_id") or "Exact-SKU-only"),
                representative=_markdown_cell(cluster.get("representative_sku") or "—"),
                count=cluster.get("exact_sku_count", 0),
                skus=_markdown_cell(", ".join(cluster.get("exact_skus") or [])),
            )
        )
    if not clusters:
        lines.append("| — | — | 0 | — |")

    low_records = [record for record in assessment.get("records", []) if record.get("severity") == "LOW"]
    lines.extend([
        "",
        "## LOW consistency findings",
        "",
        "| Exact SKU | Confirmed absent publication point(s) |",
        "|---|---|",
    ])
    for record in low_records:
        absent = [name for name, point in (record.get("publication_points") or {}).items()
                  if point.get("state") == "ABSENT"]
        lines.append(f"| {_markdown_cell(record.get('exact_sku'))} | {_markdown_cell(', '.join(absent) or '—')} |")
    if not low_records:
        lines.append("| — | — |")
    return "\n".join(lines) + "\n"
