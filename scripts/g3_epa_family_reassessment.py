"""Reapply approved shared EPA publication rules to six frozen G3 family sources."""

import argparse
from collections import Counter
from contextlib import redirect_stdout
from datetime import datetime, timezone
import importlib
import io
import json
import os
from pathlib import Path


GRADES = ("PASS", "HIGH", "MEDIUM", "LOW")


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build(manifest_path, source_root, out):
    manifest = read(manifest_path)
    if manifest.get("contract") != "G3_EPA_FAMILY_REPLAY_MANIFEST_V1":
        raise ValueError("Unsupported G3 EPA family replay manifest")
    source_root, out = Path(source_root), Path(out)
    summary = []
    for item in manifest["families"]:
        slug, family = item["slug"], item["family"]
        candidate_path = source_root / slug / item["candidate_path"]
        candidate = read(candidate_path)
        if (candidate.get("contract") != item["source_contract"]
                or candidate.get("status") != "SOURCE_CANDIDATES_READY"
                or str(candidate.get("epa_capture_run_id")) != item["source_run_id"]):
            raise ValueError(f"{family} source candidates are not bound to the selected hosted run")
        native_out = out / slug / "native"
        module = importlib.import_module(item["assessor_module"])
        with redirect_stdout(io.StringIO()):
            module.build(candidate_path, native_out)
        native = read(native_out / "energy-star-assessment.json")
        rows = native.get("records", [])
        if (native.get("status") != "PASS" or native.get("contract") != item["assessment_contract"]
                or len(rows) != candidate.get("population_count")
                or len({row.get("exact_sku") for row in rows}) != len(rows)):
            raise ValueError(f"{family} native assessment is incomplete")
        records = []
        for row in rows:
            grade = row.get("display_outcome")
            if grade not in GRADES:
                raise ValueError(f"{family} has an unresolved model: {row.get('exact_sku')}")
            records.append({**row, "grade": grade})
        counts = Counter(row["grade"] for row in records)
        report = {"contract": "G3_EPA_FAMILY_SAVED_SOURCE_REASSESSMENT_V1",
                  "status": "PASS", "family": family, "source_run_id": item["source_run_id"],
                  "assessment_run_id": os.getenv("GITHUB_RUN_ID"),
                  "captured_at": datetime.now(timezone.utc).isoformat(),
                  "sku_count": len(records),
                  "counts": {level: counts.get(level, 0) for level in GRADES},
                  "finding_count": sum(len(row["findings"]) for row in records),
                  "records": records, "overall_product_compliance": "NOT_EVALUATED"}
        path = out / slug / "assessment.json"
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        summary.append({"family": family, "slug": slug, "source_run_id": item["source_run_id"],
                        "sku_count": len(records), "counts": report["counts"]})
    result = {"contract": "G3_EPA_SAVED_SOURCE_REASSESSMENT_BUNDLE_V1", "status": "PASS",
              "assessment_run_id": os.getenv("GITHUB_RUN_ID"), "families": summary}
    (out / "summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("manifest", "source-root", "out"):
        parser.add_argument("--" + option, required=True)
    args = parser.parse_args()
    build(args.manifest, args.source_root, args.out)
