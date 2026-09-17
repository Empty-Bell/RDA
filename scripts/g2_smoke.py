"""Bounded observational smoke: whole listing, one PDP/PDF, brand EPA snapshot."""

from datetime import datetime, timezone
from dataclasses import fields
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from regaudit.config import load_configuration
from regaudit.contracts import dumps, validate_bundle, verify_evidence_files
from regaudit.facts import TYPES
from regaudit.report import summarize_bundle, verify_report_source_observations
from g2_population import observation, population_records
from source_recon import FAMILIES
from g2_pdp import select_sample, collect_samples, coverage, verify_identity
from g2_normalized import normalize_source_pdp
from g2_label_collect import collect_energyguide_documents
from g2_label_activation import (
    load_capacity_review_annotations,
    load_review_annotations,
    observe_raw_model,
    select_live_reviewed_capacity,
    select_live_reviewed_energy,
    summarize_capacity_selection_outcomes,
    summarize_selection_outcomes,
)
from g2_current_index_candidate_projection import load_replayed_rows
from g2_refrigerator_pattern_bridge import project_same_run_refrigerator_candidates
from g2_refrigerator_pattern_capture import capture_pattern_rows
from g2_energy_star_publication_points import collect_publication_points


def main():
    run_id = uuid.uuid4().hex
    out = ROOT / "runtime/g2" / run_id
    out.mkdir(parents=True, exist_ok=False)
    started = datetime.now(timezone.utc).isoformat()
    checkpoint = {
        "status": "FAILED",
        "scope": "G2 observational pilot; no assessment",
        "phase_gate": "NOT_EVALUATED",
        "run_id": run_id,
        "github_run_id": os.getenv("GITHUB_RUN_ID"),
        "github_run_attempt": os.getenv("GITHUB_RUN_ATTEMPT"),
        "git_sha": os.getenv("GITHUB_SHA"),
        "started_at": started,
        "rule_evaluation": "NOT_EVALUATED",
    }
    try:
        for script in ("source_recon.py", "epa_recon.py"):
            subprocess.run(
                [sys.executable, str(ROOT / "scripts" / script), "--family", "refrigerator"],
                cwd=ROOT,
                check=True,
                timeout=900,
            )
        source = ROOT / "runtime/source-recon/refrigerator"
        epa = ROOT / "runtime/epa-query/p5st-her9"
        recon = json.loads((source / "recon.json").read_bytes())
        epa_recon = json.loads((epa / "recon.json").read_bytes())
        for report in (recon, epa_recon):
            if (
                report["status"] != "PASS"
                or report["run_id"] != os.getenv("GITHUB_RUN_ID")
                or report["git_sha"] != os.getenv("GITHUB_SHA")
            ):
                raise ValueError("Collector failure or mixed execution provenance")
        pages = {}
        page_sources = {}
        for entry in recon["observations"]:
            if "request_body" not in entry:
                continue
            offset = int(entry["request_body"]["startIndex"])
            raw = (source / entry["fixture"]).read_bytes()
            if hashlib.sha256(raw).hexdigest() != entry["fixture_sha256"]:
                raise ValueError("PF hash mismatch")
            if offset in pages and pages[offset] != raw:
                raise ValueError("Same offset changed")
            pages[offset] = raw
            page_sources[offset] = entry["url"]
        ordered = sorted(pages)
        products, parsed = population_records(
            [pages[i] for i in ordered], run_id, FAMILIES["refrigerator"]["plp"]
        )
        config, config_hash = load_configuration(ROOT)
        label_reviews = load_review_annotations(
            ROOT / "docs/evidence/g2-label-review-annotations.json"
        )
        capacity_reviews = load_capacity_review_annotations(
            ROOT / "docs/evidence/g2-capacity-model-review.json"
        )
        label_selection_outcomes = []
        capacity_selection_outcomes = []
        bundle = {
            "manifest": {
                "schema_version": "draft-1",
                "run_id": run_id,
                "started_at": started,
                "completed_at": None,
                "git_sha": os.environ["GITHUB_SHA"],
                "config_hash": config_hash,
                "rule_version": None,
                "source_contract_version": config["sources"]["contract_version"],
                "python_version": sys.version.split()[0],
                "playwright_version": __import__(
                    "importlib.metadata", fromlist=["version"]
                ).version("playwright"),
                "runner": "ubuntu-24.04-x64",
                "overall_execution_status": "PARTIAL",
                "assessment_enabled": False,
            },
            "products": products,
            "evidence": [],
            "facts": [],
            "assessments": [],
        }

        def evidence(raw, url, sku, kind, captured_at=None):
            digest = hashlib.sha256(raw).hexdigest()
            relative = "raw/" + digest + ".bin"
            path = out / relative
            path.parent.mkdir(exist_ok=True)
            if not path.exists():
                with path.open("xb") as stream:
                    stream.write(raw)
            elif path.read_bytes() != raw:
                raise ValueError("Raw hash collision")
            identity = "e-" + str(len(bundle["evidence"]))
            bundle["evidence"].append(
                {
                    "evidence_id": identity,
                    "run_id": run_id,
                    "product_group": "refrigerator",
                    "sku": sku,
                    "source_url": url,
                    "captured_at": captured_at or started,
                    "sha256": digest,
                    "parser_version": "g2-observation-1",
                    "evidence_type": kind,
                    "relative_path": relative,
                }
            )
            return identity, digest

        for offset in ordered:
            members = {
                r["modelCode"]
                for g in json.loads(pages[offset])["searchResults"]
                for r in g["groupedProductList"]
            }
            for sku in sorted(members):
                evidence(pages[offset], page_sources[offset], sku, "projected-public-pf-response")
        pdp = json.loads((source / "pdp-observation.json").read_bytes())
        sku = pdp["target_sku"]
        if sku not in {p["exact_sku"] for p in products}:
            raise ValueError("Sample outside population")
        bridge = pdp["json_endpoints"][0]
        raw = (source / bridge["fixture"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != bridge["fixture_sha256"]:
            raise ValueError("Bridge hash mismatch")
        snapshot = json.loads((source / "fixtures/public-claim-snapshot.json").read_bytes())
        parsed_pdp = verify_identity(sku, pdp["final_url"], snapshot, json.loads(raw))
        bridge_id, bridge_hash = evidence(
            raw, bridge["url"], sku, "projected-public-bridge-response"
        )
        source_observations = {}
        for name in (
            "pdp-facts.json",
            "public-claim-facts.json",
            "fixtures/public-claim-snapshot.json",
        ):
            source_observations[name] = evidence(
                (source / name).read_bytes(), pdp["final_url"], sku, "uninterpreted-pdp-observation"
            )[0]
        claim_facts = json.loads((source / "public-claim-facts.json").read_bytes())
        normalized_pdp = normalize_source_pdp(parsed_pdp, claim_facts)
        normalization_id, _ = evidence(
            dumps(normalized_pdp).encode(), pdp["final_url"], sku, "pdp-source-normalization"
        )

        def fact(kind, values, refs, exact_sku=None):
            observations = {f.name: observation() for f in fields(TYPES[kind])}
            observations.update(values)
            bundle["facts"].append(
                {
                    "fact_id": "f-" + kind + ("-" + exact_sku if exact_sku else ""),
                    "run_id": run_id,
                    "product_group": "refrigerator",
                    "exact_sku": exact_sku or sku,
                    "kind": kind,
                    "observations": observations,
                    "evidence_ids": refs,
                }
            )

        fact(
            "PDP",
            {
                "pdp_model": observation(sku),
                "pdp_url": observation(pdp["final_url"]),
                "source_bridge_hash": observation(bridge_hash),
                **normalized_pdp["observations"],
            },
            [bridge_id, *source_observations.values(), normalization_id],
        )
        label = json.loads((source / "energyguide-observation.json").read_bytes())
        raw = (source / "energyguide-original.pdf").read_bytes()
        if not raw.startswith(b"%PDF-") or hashlib.sha256(raw).hexdigest() != label["sha256"]:
            raise ValueError("Label bytes mismatch")
        if label["requested_url"] not in {d["url"] for d in parsed_pdp["energyguide_documents"]}:
            raise ValueError("Label outside selected SKU support")
        label_id, label_hash = evidence(
            raw, label["requested_url"], sku, "original-energyguide-pdf"
        )
        extraction_id, _ = evidence(
            (source / "energyguide-observation.json").read_bytes(),
            label["requested_url"],
            sku,
            "extraction-observation",
        )
        original_candidates = json.loads(
            (source / "energyguide-field-candidates.json").read_bytes()
        )
        original_layout = json.loads((source / "energyguide-layout-candidates.json").read_bytes())
        original_candidate_refs = []
        for name in ("energyguide-field-candidates.json", "energyguide-layout-candidates.json"):
            ref, _ = evidence(
                (source / name).read_bytes(),
                label["requested_url"],
                sku,
                "unselected-label-field-candidates",
            )
            original_candidate_refs.append(ref)
        original_model_observation = observe_raw_model(original_candidates)
        original_selection = select_live_reviewed_energy(
            sku, label, original_candidates, original_layout, label_reviews
        )
        original_capacity_selection = select_live_reviewed_capacity(
            sku, label, original_candidates, capacity_reviews
        )
        original_selection_id, _ = evidence(
            dumps(
                {
                    "selection_contract": "REVIEW_BOUND_LIVE_OBSERVATION_ONLY",
                    "exact_sku": sku,
                    "pdf_sha256": label_hash,
                    "selection": original_selection,
                }
            ).encode(),
            label["requested_url"],
            sku,
            "review-bound-label-selection",
        )
        original_capacity_selection_id, _ = evidence(
            dumps(
                {
                    "selection_contract": "REVIEW_BOUND_LIVE_CAPACITY_OBSERVATION_ONLY",
                    "exact_sku": sku,
                    "pdf_sha256": label_hash,
                    "selection": original_capacity_selection,
                }
            ).encode(),
            label["requested_url"],
            sku,
            "review-bound-label-capacity-selection",
        )
        # The original source_recon collector retrieves its single declared document.
        label_selection_outcomes.append(
            {
                "exact_sku": sku,
                "source_document_index": 0,
                "pdf_sha256": label_hash,
                "selection": original_selection,
            }
        )
        capacity_selection_outcomes.append(
            {
                "exact_sku": sku,
                "source_document_index": 0,
                "pdf_sha256": label_hash,
                "selection": original_capacity_selection,
            }
        )
        fact(
            "ENERGYGUIDE",
            {
                "document_url": observation(label["requested_url"]),
                "document_sha256": observation(label_hash),
                "document_status": observation("SOURCE_PDF_PARSED"),
                "extraction_engine": observation(label["extraction_engine"]),
                "embedded_text": observation(label["embedded_text"]),
                "ocr_raw_text": observation("\n".join(label["ocr_raw_texts"])),
                "label_model_raw": original_model_observation["observation"],
                "annual_energy_kwh": original_selection["observation"],
                "capacity": original_capacity_selection["observation"],
                "fallback_reason": observation(label["fallback_reason"]),
                "ocr_scale": observation(label["ocr_scale"]),
            },
            [
                label_id,
                extraction_id,
                *original_candidate_refs,
                original_selection_id,
                original_capacity_selection_id,
            ],
        )
        # Dataset-query context is not evidence of a product certification match.
        for entry in epa_recon["responses"]:
            path = epa / (entry["name"] + "-response.bin")
            if path.exists():
                raw = path.read_bytes()
                if hashlib.sha256(raw).hexdigest() != entry["body_sha256"]:
                    raise ValueError("EPA response hash mismatch")
                evidence(raw, entry["url"], sku, "epa-dataset-query-context-not-sku-match")
        for domain in ("FTC", "EPA"):
            bundle["assessments"].append(
                {
                    "assessment_id": "a-" + domain,
                    "run_id": run_id,
                    "product_group": "refrigerator",
                    "exact_sku": sku,
                    "regulatory_domain": domain,
                    "control_id": "PILOT_COLLECTION_SCOPE",
                    "rule_id": None,
                    "rule_version": None,
                    "assessment_status": "NOT_EVALUATED",
                    "severity": None,
                    "issue_code": None,
                    "reason": "Rule evaluation disabled; dataset context does not establish certification match",
                    "expected": None,
                    "observed": None,
                    "evidence_ids": [bridge_id] if domain == "FTC" else [],
                    "automatic_final_legal_conclusion": False,
                }
            )
        # The collection budget is bounded independently of the observed population.
        # Coverage still records every unattempted SKU rather than treating this cap as
        # a population or assessment-completion threshold.
        selected = select_sample(products, sku, limit=10)
        samples = [
            {
                "exact_sku": sku,
                "status": "VERIFIED_EXACT_IDENTITY",
                "bridge": {"url": bridge["url"], "sha256": bridge_hash},
                "pdp_facts_raw": parsed_pdp,
            }
        ]
        samples.extend(
            collect_samples([p for p in selected if p["exact_sku"] != sku], out / "pdp-samples")
        )
        current_index_dir = out / "epa-current-index"
        current_index_env = {**os.environ, "RDA_EXECUTION_ID": run_id}
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "g2_epa_current_index_samsung_capture.py"),
                "--out",
                str(current_index_dir),
            ],
            cwd=ROOT,
            env=current_index_env,
            check=True,
            timeout=900,
        )
        current_index_scan, current_index_rows = load_replayed_rows(current_index_dir)
        current_index_projection = project_same_run_refrigerator_candidates(
            samples, current_index_scan, current_index_rows, run_id
        )
        (out / "current-index-target-feed.json").write_text(
            dumps(current_index_projection["target_feed"]), encoding="utf-8"
        )
        (out / "current-index-candidates.json").write_text(
            dumps(current_index_projection["candidate_projection"]), encoding="utf-8"
        )
        pattern_bridge = capture_pattern_rows(
            out / "epa-refrigerator-pattern-bridge",
            current_index_projection["target_feed"],
            current_index_projection["candidate_projection"],
            execution_id=run_id,
        )
        plp_observation_path = source / "plp-claim-observation.json"
        plp_observation = json.loads(plp_observation_path.read_bytes())
        cards = plp_observation.get("cards")
        if not isinstance(cards, list):
            raise ValueError("PLP visual observation has invalid cards")
        visual_snapshots = {sku: snapshot}
        for result in samples[1:]:
            for entry in result.get("observations", []):
                if Path(entry.get("path", "")).name == "snapshot.json":
                    visual_snapshots[result["exact_sku"]] = json.loads(
                        Path(entry["path"]).read_bytes()
                    )
        # Keep direct PF/Bridge declarations distinct from the three visual points.
        # These values can later be collected without a browser, but they do not by
        # themselves assert that a logo or a rendered table was visible.
        source_declarations = {
            record["exact_sku"]: {
                "plp_energy_star_flag_raw": record.get("plp_energy_star_claim_raw"),
            }
            for record in parsed.get("records", [])
            if isinstance(record.get("exact_sku"), str)
        }
        for result in samples:
            declaration = source_declarations.setdefault(result["exact_sku"], {})
            facts = result.get("pdp_facts_raw")
            declaration["pdp_energy_star_spec_rows_raw"] = (
                facts.get("energy_star_spec_claim_raw", []) if isinstance(facts, dict) else []
            )
        publication_points = collect_publication_points(
            cards, samples, visual_snapshots, source_declarations
        )
        (out / "energy-star-publication-points.json").write_text(
            dumps(publication_points), encoding="utf-8"
        )
        # Preserve the unmodified PLP DOM observation independently of its three-point projection.
        for result in samples:
            evidence(
                plp_observation_path.read_bytes(),
                page_sources[ordered[0]],
                result["exact_sku"],
                "plp-visual-publication-observation",
            )
        for result in samples[1:]:
            refs = {}
            for entry in result["responses"] + result["observations"]:
                if "path" not in entry:
                    continue
                raw = Path(entry["path"]).read_bytes()
                if hashlib.sha256(raw).hexdigest() != entry["sha256"]:
                    raise ValueError("Per-SKU response bytes changed")
                ref, digest = evidence(
                    raw,
                    entry["url"],
                    result["exact_sku"],
                    "per-sku-pdp-public-observation",
                    entry["captured_at"],
                )
                refs[entry["path"]] = (ref, digest)
            evidence(
                dumps(result).encode(),
                result.get("final_url", result["requested_url"]),
                result["exact_sku"],
                "pdp-collection-result",
            )
            if result["status"] == "VERIFIED_EXACT_IDENTITY":
                ref, digest = refs[result["bridge"]["path"]]
                normalized_pdp = normalize_source_pdp(result["pdp_facts_raw"], None)
                normalization_ref, _ = evidence(
                    dumps(normalized_pdp).encode(),
                    result["final_url"],
                    result["exact_sku"],
                    "pdp-source-normalization",
                )
                fact(
                    "PDP",
                    {
                        "pdp_model": observation(result["exact_sku"]),
                        "pdp_url": observation(result["final_url"]),
                        "source_bridge_hash": observation(digest),
                        **normalized_pdp["observations"],
                    },
                    [
                        *dict.fromkeys(
                            [ref, *[item[0] for item in refs.values()], normalization_ref]
                        )
                    ],
                    result["exact_sku"],
                )
        labels = collect_energyguide_documents(
            [result for result in samples[1:] if result["status"] == "VERIFIED_EXACT_IDENTITY"],
            out / "energyguide-samples",
        )
        if any(result["status"] == "FAILED" for result in labels):
            raise ValueError("Expanded EnergyGuide observation failed")
        label_fact_inputs = {}
        for result in labels:
            folder = (
                out
                / "energyguide-samples"
                / result["exact_sku"]
                / str(result["source_document_index"])
            )
            raw = (folder / "energyguide-original.pdf").read_bytes()
            if hashlib.sha256(raw).hexdigest() != result["sha256"]:
                raise ValueError("Expanded label bytes changed")
            label_id, label_hash = evidence(
                raw,
                result["final_url"],
                result["exact_sku"],
                "original-energyguide-pdf",
                result["captured_at"],
            )
            observation_id, _ = evidence(
                (folder / "result.json").read_bytes(),
                result["final_url"],
                result["exact_sku"],
                "extraction-observation",
                result["captured_at"],
            )
            candidate_refs = []
            candidate_documents = {}
            for name in ("energyguide-field-candidates.json", "energyguide-layout-candidates.json"):
                candidate_documents[name] = json.loads((folder / name).read_bytes())
                ref, _ = evidence(
                    (folder / name).read_bytes(),
                    result["final_url"],
                    result["exact_sku"],
                    "unselected-label-field-candidates",
                    result["captured_at"],
                )
                candidate_refs.append(ref)
            selection = select_live_reviewed_energy(
                result["exact_sku"],
                result,
                candidate_documents["energyguide-field-candidates.json"],
                candidate_documents["energyguide-layout-candidates.json"],
                label_reviews,
            )
            capacity_selection = select_live_reviewed_capacity(
                result["exact_sku"],
                result,
                candidate_documents["energyguide-field-candidates.json"],
                capacity_reviews,
            )
            model_observation = observe_raw_model(
                candidate_documents["energyguide-field-candidates.json"]
            )
            selection_ref, _ = evidence(
                dumps(
                    {
                        "selection_contract": "REVIEW_BOUND_LIVE_OBSERVATION_ONLY",
                        "exact_sku": result["exact_sku"],
                        "pdf_sha256": label_hash,
                        "selection": selection,
                    }
                ).encode(),
                result["final_url"],
                result["exact_sku"],
                "review-bound-label-selection",
                result["captured_at"],
            )
            capacity_selection_ref, _ = evidence(
                dumps(
                    {
                        "selection_contract": "REVIEW_BOUND_LIVE_CAPACITY_OBSERVATION_ONLY",
                        "exact_sku": result["exact_sku"],
                        "pdf_sha256": label_hash,
                        "selection": capacity_selection,
                    }
                ).encode(),
                result["final_url"],
                result["exact_sku"],
                "review-bound-label-capacity-selection",
                result["captured_at"],
            )
            label_selection_outcomes.append(
                {
                    "exact_sku": result["exact_sku"],
                    "source_document_index": result["source_document_index"],
                    "pdf_sha256": label_hash,
                    "selection": selection,
                }
            )
            capacity_selection_outcomes.append(
                {
                    "exact_sku": result["exact_sku"],
                    "source_document_index": result["source_document_index"],
                    "pdf_sha256": label_hash,
                    "selection": capacity_selection,
                }
            )
            label_fact_inputs.setdefault(result["exact_sku"], []).append(
                (
                    result,
                    label_hash,
                    [
                        label_id,
                        observation_id,
                        *candidate_refs,
                        selection_ref,
                        capacity_selection_ref,
                    ],
                    selection["observation"],
                    capacity_selection["observation"],
                    model_observation["observation"],
                )
            )
        for label_sku, inputs in label_fact_inputs.items():
            # Multiple Support PDFs remain evidence only until a document-selection policy exists.
            if len(inputs) != 1:
                continue
            result, label_hash, refs, annual_energy, capacity, label_model_raw = inputs[0]
            fact(
                "ENERGYGUIDE",
                {
                    "document_url": observation(result["final_url"]),
                    "document_sha256": observation(label_hash),
                    "document_status": observation("SOURCE_PDF_PARSED"),
                    "extraction_engine": observation(result["extraction_engine"]),
                    "embedded_text": observation(result["embedded_text"]),
                    "ocr_raw_text": observation("\n".join(result["ocr_raw_texts"])),
                    "label_model_raw": label_model_raw,
                    "annual_energy_kwh": annual_energy,
                    "capacity": capacity,
                    "fallback_reason": observation(result["fallback_reason"]),
                    "ocr_scale": observation(result["ocr_scale"]),
                },
                refs,
                label_sku,
            )
        pdp_coverage = coverage(products, samples)
        label_selection_summary = summarize_selection_outcomes(label_selection_outcomes)
        capacity_selection_summary = summarize_capacity_selection_outcomes(
            capacity_selection_outcomes
        )
        with (out / "pdp-coverage.json").open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(dumps(pdp_coverage))
        bundle["manifest"]["completed_at"] = datetime.now(timezone.utc).isoformat()
        validate_bundle(bundle)
        verify_evidence_files(bundle, out)
        report = summarize_bundle(bundle)
        verify_report_source_observations(bundle, report)
        for name, data in [("bundle.json", bundle), ("report.json", report)]:
            with (out / name).open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(dumps(data))
        checkpoint.update(
            status="PASS" if not pdp_coverage["counts"]["FAILED"] else "FAILED",
            population_groups=parsed["total_groups"],
            population_skus=len(products),
            collected_pdp_skus=[
                r["exact_sku"] for r in samples if r["status"] == "VERIFIED_EXACT_IDENTITY"
            ],
            attempted_pdp_skus=[r["exact_sku"] for r in samples],
            pdp_coverage_counts=pdp_coverage["counts"],
            pdp_coverage_sha256=hashlib.sha256(
                (out / "pdp-coverage.json").read_bytes()
            ).hexdigest(),
            collected_label_skus=sorted({sku, *[result["exact_sku"] for result in labels]}),
            epa_brand_scan=epa_recon["brand_scan"],
            label_selection_summary=label_selection_summary,
            capacity_selection_summary=capacity_selection_summary,
            sku_certification_matching="NOT_EVALUATED",
            current_index_candidate_projection={
                "target_count": len(current_index_projection["target_feed"]["targets"]),
                "record_count": len(current_index_projection["candidate_projection"]["records"]),
                "states": [
                    record["candidate_projection_state"]
                    for record in current_index_projection["candidate_projection"]["records"]
                ],
            },
            current_index_pattern_bridge={
                "compatible_pattern_candidate_count": pattern_bridge[
                    "compatible_pattern_candidate_count"
                ],
                "bridge_count": len(pattern_bridge["bridges"]),
                "states": [
                    bridge["pattern_candidate_state"] for bridge in pattern_bridge["bridges"]
                ],
            },
            energy_star_publication_points={
                "sampled_sku_count": len(publication_points["records"]),
                "point_states": publication_points["states"],
                "assessment_status": "NOT_EVALUATED",
            },
            bundle_sha256=hashlib.sha256((out / "bundle.json").read_bytes()).hexdigest(),
        )
    except Exception as error:
        checkpoint["error_class"] = type(error).__name__
        print("G2_PILOT_FAILED: " + str(error), file=sys.stderr)
    finally:
        (out / "checkpoint.json").write_text(dumps(checkpoint), encoding="utf-8")
    return 0 if checkpoint["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
