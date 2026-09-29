"""Project source-backed model evidence into the wide operational report."""

import json
import re


HEADERS = [
    "No.", "Product Family", "SKU", "PDP URL", "Severity", "Issue Type",
    "Status", "EnergyGuide PDF Link", "EG Link Status", "PDP kWh",
    "PDP Capacity (cu.ft)", "PLP E-STAR", "PDP E-STAR Badge", "PDP Spec E-STAR",
    "OCR Model", "OCR kWh", "OCR Capacity (cu.ft)", "OCR Status", "EPA kWh",
    "EPA Capacity (cu.ft)", "EPA Status", "EPA Match", "Description",
]

ACTION = {
    "SAMSUNG_ENERGY_STAR_SOURCE_CONFLICT": ("Align ENERGY STAR claims across PDP, PLP and specifications.", "PDP·PLP·Specs의 ENERGY STAR 표기를 대조해 일치시키세요."),
    "CRITICAL_ENERGY_STAR_ELIGIBILITY_CANDIDATE": ("Check the EPA registration supporting the ENERGY STAR claim.", "ENERGY STAR 표시의 EPA 등록 근거를 확인하세요."),
    "PDP_ANNUAL_ENERGY_MISSING": ("Verify and complete the PDP annual energy disclosure.", "PDP의 연간 에너지 공개값을 확인하고 보완하세요."),
    "PDP_ENERGYGUIDE_CAPACITY_MISMATCH": ("Verify the PDP and EnergyGuide capacity values and correct the inaccurate disclosure.", "PDP와 EnergyGuide의 용량을 대조하고 잘못된 공개값을 수정하세요."),
    "EPA_CURRENT_MODEL_NOT_REGISTERED": ("Check current EPA registration and the ENERGY STAR claim together.", "현행 EPA 등록과 ENERGY STAR 표시를 함께 확인하세요."),
    "ANNUAL_ENERGY_MISMATCH": ("Compare PDP, EnergyGuide and EPA annual kWh values and correct the differing value.", "PDP·EnergyGuide·EPA의 연간 kWh를 대조하고 잘못된 값을 수정하세요."),
    "ENERGY_STAR_PUBLICATION_INCONSISTENT": ("Align ENERGY STAR claims across PDP, PLP and specifications.", "PDP·PLP·Specs의 ENERGY STAR 표기를 대조해 일치시키세요."),
    "ENERGYGUIDE_DOCUMENT_MISSING_CANDIDATE": ("Add or reconnect the EnergyGuide document for this SKU.", "해당 SKU의 EnergyGuide 문서를 연결하거나 링크를 수정하세요."),
}


def korean_description(description):
    for english, korean in ACTION.values():
        description = description.replace(english, korean)
    replacements = (
        ("[Basis] No automated issues found", "[근거] 자동 판정 이슈 없음"),
        ("[Basis] ", "[근거] "), ("[Comparison]", "[비교]"),
        ("[Mismatch]", "[불일치]"),
        ("[Action]", "[조치]"),
        ("Model: OCR=", "모델: OCR="), ("Capacity: OCR=", "용량: OCR="),
        ("; assessment=", "; 판정="), (" vs PDP=", " / PDP="),
        (" -> MATCH", " → 일치"), (" -> DIFFERENT", " → 차이"),
        ("not assessed", "미판정"),
    )
    for original, translated in replacements:
        description = description.replace(original, translated)
    return description


def observed(source, key):
    field = source.get(key) or {}
    return field.get("value") if field.get("state") == "VALUE" else None


def number(value):
    if value is None:
        return None
    match = re.search(r"(?<!\w)(\d+(?:\.\d+)?)\s*(?:kwh|cu\.?\s*ft|cubic\s+feet)\b", str(value), re.I)
    return float(match.group(1)) if match else None


def energy_number(value):
    result = number(value)
    if result is not None or not value:
        return result
    match = re.search(r"(?:annual\s+energy|energy\s+(?:usage|consumption)|kwh\s*/\s*(?:year|yr))[^:·]*:\s*(\d+(?:\.\d+)?)", str(value), re.I)
    return float(match.group(1)) if match else None


def pdp_capacity(value):
    if not value:
        return None
    match = re.search(r"(?:Total|Net Total|Capacity)\s*(?:Capacity)?\s*\([^)]*\)\s*:\s*(\d+(?:\.\d+)?)", str(value), re.I)
    return float(match.group(1)) if match else None


def display_number(value):
    return None if value is None else int(value) if value == int(value) else value


def projection(record, detail, position):
    raw = record.get("raw_summary") or {}
    assessment = detail.get("assessment") or {}
    frozen = detail.get("frozen_canonical_source_row") or {}
    observations = frozen.get("energyguide_source_observations") or []
    observation = observations[0] if observations else {}
    ocr_energy = observed(observation, "annual_energy_kwh")
    ocr_capacity = observed(observation, "capacity")
    ocr_model = observed(observation, "label_model_raw")
    document_status = observed(observation, "document_status")
    label_url = (record.get("label_urls") or [None])[0]
    if not label_url:
        eg_status = "MISSING"
    elif document_status == "SOURCE_PDF_PARSED":
        eg_status = "OK"
    else:
        eg_status = "LINKED_UNVERIFIED"
    registration = (assessment.get("energy_star_publication") or {}).get("epa_current_index_registration") or {}
    candidates = registration.get("candidates") or []
    pdp_kwh = energy_number(raw.get("pdp_energy"))
    label_kwh = (ocr_energy or {}).get("amount") if isinstance(ocr_energy, dict) else number(raw.get("label_energy"))
    label_capacity = (ocr_capacity or {}).get("amount") if isinstance(ocr_capacity, dict) else number(raw.get("label_capacity"))
    epa_kwh = number(raw.get("epa_energy"))
    epa_capacity = number(raw.get("epa_capacity"))
    numeric_findings = (assessment.get("energyguide_numeric") or {}).get("findings") or []
    for finding in numeric_findings:
        evidence = finding.get("evidence") or {}
        if finding.get("field") == "annual_energy_kwh":
            label_kwh = label_kwh if label_kwh is not None else evidence.get("label_amount")
            epa_kwh = epa_kwh if epa_kwh is not None else evidence.get("epa_amount")
        if finding.get("field") == "capacity_cu_ft":
            label_capacity = label_capacity if label_capacity is not None else evidence.get("label_amount")
            epa_capacity = epa_capacity if epa_capacity is not None else evidence.get("epa_amount")
    ocr_model = ocr_model or raw.get("label_model")
    issue_codes = sorted({item["issue_code"] for item in record.get("findings", []) if item.get("issue_code")})
    grade = record["grade"]
    basis = "No automated issues found" if not issue_codes else ", ".join(issue_codes)
    comparisons = []
    model_assessment = (assessment.get("energyguide_model_pattern") or {}).get("assessment")
    if ocr_model:
        comparisons.append(f"Model: OCR={str(ocr_model).replace(chr(10), ', ')}; PDP={raw.get('pdp_model') or record['model']}; assessment={model_assessment or 'not assessed'}")
    if pdp_kwh is not None and label_kwh is not None:
        comparisons.append(f"kWh: OCR={display_number(label_kwh)} vs PDP={display_number(pdp_kwh)} -> {'MATCH' if label_kwh == pdp_kwh else 'DIFFERENT'}")
    capacity = pdp_capacity(raw.get("pdp_capacity"))
    if capacity is not None and label_capacity is not None:
        comparisons.append(f"Capacity: OCR={display_number(label_capacity)} vs PDP={display_number(capacity)} -> {'MATCH' if label_capacity == capacity else 'DIFFERENT'}")
    ocr_status = ("OCR_NUMERIC_DIFFERENCE" if numeric_findings else "OCR_PARSED") if document_status == "SOURCE_PDF_PARSED" else (raw.get("label_energy_state") or "NOT_CAPTURED")
    description = "[Basis] " + basis
    if comparisons:
        description += "\n[Comparison]\n  " + "\n  ".join(comparisons)
    if issue_codes:
        description += "\n[Mismatch] " + ", ".join(issue_codes)
        action_text = list(dict.fromkeys(ACTION.get(code, ("Review source evidence for the flagged control.", "표시된 판정 항목의 원본 근거를 확인하세요."))[0] for code in issue_codes))
        description += "\n[Action] " + " ".join(action_text)
    listings = frozen.get("listings") or []
    status = "LISTED" if listings else "IN_SCOPE"
    return {
        "No.": position, "Product Family": record["family"], "SKU": record["model"],
        "PDP URL": record.get("pdp_url"), "Severity": grade,
        "Issue Type": ", ".join(issue_codes) if issue_codes else "NO_AUTOMATED_EXCEPTION",
        "Status": status, "EnergyGuide PDF Link": label_url, "EG Link Status": eg_status,
        "PDP kWh": display_number(pdp_kwh), "PDP Capacity (cu.ft)": display_number(capacity),
        "PLP E-STAR": (record.get("points") or {}).get("plp_logo") or raw.get("plp_logo"),
        "PDP E-STAR Badge": (record.get("points") or {}).get("pdp_logo") or raw.get("pdp_logo"),
        "PDP Spec E-STAR": (record.get("points") or {}).get("spec_certification"),
        "OCR Model": ocr_model, "OCR kWh": display_number(label_kwh),
        "OCR Capacity (cu.ft)": display_number(label_capacity),
        "OCR Status": ocr_status,
        "EPA kWh": display_number(epa_kwh), "EPA Capacity (cu.ft)": display_number(epa_capacity),
        "EPA Status": registration.get("state") or raw.get("epa_registration") or record.get("epa_registration"),
        "EPA Match": json.dumps(candidates, ensure_ascii=False) if candidates else raw.get("epa_match_status"),
        "Description": description,
    }
