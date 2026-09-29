"""Catch report projection/schema regressions before live source collection."""

import argparse
import json
from pathlib import Path

from report_projection import HEADERS, projection


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docs", type=Path, default=Path("docs"))
    args = parser.parse_args()
    model = json.loads((args.docs / "model-data.json").read_text(encoding="utf-8"))
    records = model.get("records") or []
    if not records:
        raise ValueError("Published model snapshot is empty")
    for position, record in enumerate(records, 1):
        evidence = args.docs / record["evidence_url"].removeprefix("./")
        detail = json.loads(evidence.read_text(encoding="utf-8"))
        row = projection(record, detail, position)
        if set(row) != set(HEADERS) or row["SKU"] != record["model"]:
            raise ValueError(f"Report projection contract differs for {record['family']} {record['model']}")
        if "assessment=not assessed" in row["Description"]:
            raise ValueError(f"Unhelpful model assessment leaked for {record['model']}")
    print(json.dumps({"status": "PASS", "models": len(records), "columns": len(HEADERS)}))


if __name__ == "__main__":
    main()
