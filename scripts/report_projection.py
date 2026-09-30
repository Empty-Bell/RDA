"""Project source-backed model evidence into the wide operational report."""

import json
import re


HEADERS = [
    "No.", "Product Family", "SKU", "PDP URL", "Severity", "Issue Type",
    "Status", "EnergyGuide PDF Link", "EG Link Status", "PDP kWh",
    "PDP Capacity (cu.ft)", "PLP E-STAR", "PDP E-STAR Badge", "PDP Spec E-STAR",
    "OCR Model", "OCR kWh", "OCR Capacity (cu.ft)", "OCR Status", "EPA kWh",
    "EPA Capacity (cu.ft)", "EPA Status", "EPA Model", "EPA Match", "Description",
]

# Product families for which this audit collects EnergyGuide evidence.
EG_FAMILIES = {"냉장고", "식기세척기", "세탁기", "의류건조기", "TV"}
EPA_CANDIDATE_KEYS = (
    "epa_current_model_matches", "epa_current_matches_raw", "epa_candidates_raw",
    "range_model_pattern_candidates", "range_epa_pattern_candidates",
    "cooktop_model_pattern_candidates", "cooktop_epa_pattern_candidates",
    "dryer_model_pattern_candidates", "dryer_epa_model_pattern_candidates",
    "combo_model_candidates", "combo_epa_model_pattern_candidates",
    "epa_display_pattern_candidates", "epa_computer_model_pattern_candidates",
)

ACTION = {
    "SAMSUNG_ENERGY_STAR_SOURCE_CONFLICT": ("Align ENERGY STAR claims across PDP, PLP and specifications.", "PDP·PLP·Specs의 ENERGY STAR 표기를 대조해 일치시키세요."),
    "CRITICAL_ENERGY_STAR_ELIGIBILITY_CANDIDATE": ("Check the EPA registration supporting the ENERGY STAR claim.", "ENERGY STAR 표시의 EPA 등록 근거를 확인하세요."),
    "PDP_ANNUAL_ENERGY_MISSING": ("Verify and complete the PDP annual energy disclosure.", "PDP의 연간 에너지 공개값을 확인하고 보완하세요."),
    "PDP_ENERGYGUIDE_CAPACITY_MISMATCH": ("Verify the PDP and EnergyGuide capacity values and correct the inaccurate disclosure.", "PDP와 EnergyGuide의 용량을 대조하고 잘못된 공개값을 수정하세요."),
    "EPA_CURRENT_MODEL_NOT_REGISTERED": ("Check current EPA registration and the ENERGY STAR claim together.", "현행 EPA 등록과 ENERGY STAR 표시를 함께 확인하세요."),
    "ANNUAL_ENERGY_MISMATCH": ("Compare PDP, EnergyGuide and EPA annual kWh values and correct the differing value.", "PDP·EnergyGuide·EPA의 연간 kWh를 대조하고 잘못된 값을 수정하세요."),
    "ENERGY_STAR_PUBLICATION_INCONSISTENT": ("Align ENERGY STAR claims across PDP, PLP and specifications.", "PDP·PLP·Specs의 ENERGY STAR 표기를 대조해 일치시키세요."),
    "ENERGYGUIDE_DOCUMENT_MISSING_CANDIDATE": ("Add or reconnect the EnergyGuide document for this SKU.", "해당 SKU의 EnergyGuide 문서를 연결하거나 링크를 수정하세요."),
    "ENERGYGUIDE_FILE_NOT_READABLE_CANDIDATE": ("Replace the unreadable EnergyGuide PDF or repair its link.", "열 수 없는 EnergyGuide PDF를 교체하거나 링크를 수정하세요."),
    "MODEL_IDENTITY_MISMATCH": ("Check every printed label model against the PDP SKU and correct the label link if needed.", "라벨에 적힌 모든 모델과 PDP SKU를 대조하고 잘못 연결된 라벨을 수정하세요."),
}


def korean_description(description):
    for english, korean in ACTION.values():
        description = description.replace(english, korean)
    replacements = (
        ("[Basis] No automated issues found", "[근거] 자동 판정 이슈 없음"),
        ("[Basis] ", "[근거] "), ("[Comparison]", "[비교]"),
        ("[Action]", "[조치]"),
        ("EPA registration=", "EPA 등록="), ("EPA model=", "EPA 모델="),
        ("PDP logo=", "PDP 로고="), ("PLP logo=", "PLP 로고="),
        ("PDP spec=", "PDP Specs="),
        ("PDP model=", "PDP 모델="), ("EnergyGuide models=", "EnergyGuide 모델="),
        ("model comparison=", "모델 대조="),
        ("Annual kWh:", "연간 kWh:"), ("PDP annual kWh=", "PDP 연간 kWh="),
        ("Capacity (cu.ft):", "용량 (cu.ft):"),
        ("EnergyGuide link=", "EnergyGuide 링크="),
        ("link status=", "링크 상태="), ("OCR status=", "OCR 상태="),
        ("not observed", "수집되지 않음"),
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


def epa_candidates(detail, assessment):
    publication = assessment.get("energy_star_publication") or {}
    index = publication.get("epa_current_index_registration") or {}
    containers = (index, assessment, assessment.get("epa_current_registration") or {},
                  publication.get("epa_current_registration") or {},
                  detail.get("source_comparison") or {}, detail.get("frozen_source_candidate") or {},
                  detail.get("source_candidate") or {})
    for container in containers:
        if not isinstance(container, dict):
            continue
        for key in ("candidates", *EPA_CANDIDATE_KEYS):
            rows = container.get(key)
            if isinstance(rows, list) and rows:
                return rows
    return []


def candidate_number(candidates, keys):
    values = set()
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        for key in keys:
            raw = candidate.get(key)
            if raw is None:
                continue
            try:
                values.add(float(raw))
            except (TypeError, ValueError):
                pass
            break
    return next(iter(values)) if len(values) == 1 else None


def describe(issue_codes, values, model_assessment=None):
    if not issue_codes:
        return "[Basis] No automated issues found"
    lines = []
    def shown(value):
        return "not observed" if value is None or value == "" else str(value).replace("\n", ", ")
    star_codes = {"CRITICAL_ENERGY_STAR_ELIGIBILITY_CANDIDATE",
                  "EPA_CURRENT_MODEL_NOT_REGISTERED", "SAMSUNG_ENERGY_STAR_SOURCE_CONFLICT",
                  "ENERGY_STAR_PUBLICATION_INCONSISTENT"}
    if star_codes.intersection(issue_codes):
        lines.append("EPA registration={}; EPA model={}; PDP logo={}; PLP logo={}; PDP spec={}".format(
            *(shown(values[key]) for key in ("EPA Status", "EPA Model", "PDP E-STAR Badge",
                                               "PLP E-STAR", "PDP Spec E-STAR"))))
    if "MODEL_IDENTITY_MISMATCH" in issue_codes:
        line = f"PDP model={shown(values['SKU'])}; EnergyGuide models={shown(values['OCR Model'])}"
        if model_assessment:
            line += f"; model comparison={model_assessment}"
        lines.append(line)
    if "ANNUAL_ENERGY_MISMATCH" in issue_codes:
        lines.append("Annual kWh: PDP={}; EnergyGuide={}; EPA={}".format(
            *(shown(values[key]) for key in ("PDP kWh", "OCR kWh", "EPA kWh"))))
    if "PDP_ANNUAL_ENERGY_MISSING" in issue_codes:
        lines.append("PDP annual kWh={}; EnergyGuide kWh={}; EPA kWh={}".format(
            *(shown(values[key]) for key in ("PDP kWh", "OCR kWh", "EPA kWh"))))
    if "PDP_ENERGYGUIDE_CAPACITY_MISMATCH" in issue_codes:
        lines.append("Capacity (cu.ft): PDP={}; EnergyGuide={}; EPA={}".format(
            *(shown(values[key]) for key in ("PDP Capacity (cu.ft)", "OCR Capacity (cu.ft)",
                                               "EPA Capacity (cu.ft)"))))
    if {"ENERGYGUIDE_DOCUMENT_MISSING_CANDIDATE", "ENERGYGUIDE_FILE_NOT_READABLE_CANDIDATE"}.intersection(issue_codes):
        lines.append("EnergyGuide link={}; link status={}; OCR status={}".format(
            *(shown(values[key]) for key in ("EnergyGuide PDF Link", "EG Link Status", "OCR Status"))))
    actions = list(dict.fromkeys(ACTION.get(code, ("Review source evidence for the flagged control.",))[0]
                                 for code in issue_codes))
    return ("[Basis] " + ", ".join(issue_codes)
            + ("\n[Comparison]\n  " + "\n  ".join(lines) if lines else "")
            + "\n[Action] " + " ".join(actions))


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
    eg_applicable = record["family"] in EG_FAMILIES
    label_url = (record.get("label_urls") or [None])[0] if eg_applicable else None
    if not eg_applicable:
        eg_status = None
    elif not label_url:
        eg_status = "MISSING"
    elif document_status == "SOURCE_PDF_PARSED":
        eg_status = "OK"
    else:
        eg_status = "LINKED_UNVERIFIED"
    registration = (assessment.get("energy_star_publication") or {}).get("epa_current_index_registration") or {}
    candidates = epa_candidates(detail, assessment)
    epa_model = raw.get("epa_model")
    epa_numeric = detail.get("source_epa_numeric") or {}
    pdp_kwh = energy_number(raw.get("pdp_energy"))
    label_kwh = (ocr_energy or {}).get("amount") if isinstance(ocr_energy, dict) else None
    if label_kwh is None:
        label_kwh = number(raw.get("label_energy"))
    if label_kwh is None and re.fullmatch(r"\d+(?:\.\d+)?", str(raw.get("label_energy") or "")):
        label_kwh = float(raw["label_energy"])
    label_capacity = (ocr_capacity or {}).get("amount") if isinstance(ocr_capacity, dict) else number(raw.get("label_capacity"))
    annual_value = epa_numeric.get("annual_energy_kwh") or {}
    epa_kwh = (annual_value.get("amount") if annual_value.get("state") == "VALUE"
               else None if epa_numeric else number(raw.get("epa_energy")))
    capacity_value = epa_numeric.get("capacity_cu_ft") or {}
    epa_capacity = (capacity_value.get("amount") if capacity_value.get("state") == "VALUE"
                    else None if epa_numeric else number(raw.get("epa_capacity")))
    family_rows = detail.get("source_epa_family") or []
    if family_rows:
        if epa_kwh is None:
            epa_kwh = number(family_rows[0].get("annual_energy_use_kwh_yr"))
        if epa_capacity is None:
            epa_capacity = number(family_rows[0].get("capacity_total_volume_ft3"))
    if epa_kwh is None and not epa_numeric:
        epa_kwh = candidate_number(candidates, ("annual_energy_consumption_kwh_yr_raw",
                                                "annual_energy_kwh_decimal_candidate", "annual_energy_raw",
                                                "annual_energy_use_kwh_yr", "annual_energy_use_kwh_yr_raw"))
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
    model_assessment = (assessment.get("energyguide_model_pattern") or {}).get("assessment")
    capacity = pdp_capacity(raw.get("pdp_capacity"))
    if not eg_applicable:
        ocr_status = None
    elif document_status == "SOURCE_PDF_PARSED":
        ocr_status = "OCR_NUMERIC_DIFFERENCE" if numeric_findings else "OCR_PARSED"
    elif label_kwh is not None:
        ocr_status = "VALUE"
    else:
        ocr_status = raw.get("label_energy_state") or "NOT_CAPTURED"
    listings = frozen.get("listings") or []
    status = "LISTED" if listings else "IN_SCOPE"
    values = {
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
        "EPA Model": epa_model,
        "EPA Match": (json.dumps(candidates, ensure_ascii=False) if candidates
                      else raw.get("epa_match_status") or
                      ("REGISTERED_MODEL_OBSERVED" if record.get("epa_registration") == "PRESENT" and epa_model else None)),
    }
    values["Description"] = describe(issue_codes, values, model_assessment)
    return values
