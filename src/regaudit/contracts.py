"""Strict draft data envelopes and same-run evidence graph validation."""

from dataclasses import dataclass, fields
from datetime import datetime
from enum import Enum
import json
from pathlib import Path, PurePosixPath
import hashlib
import re
from typing import Any, TypeGuard, TypeVar, cast

T = TypeVar("T")


class ContractError(ValueError):
    pass


class ObservationState(str, Enum):
    VALUE = "VALUE"
    MISSING = "MISSING"
    NOT_OBSERVED = "NOT_OBSERVED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    ERROR = "ERROR"


class PipelineStatus(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    OUTPUT_MISSING = "OUTPUT_MISSING"


class AssessmentStatus(str, Enum):
    NO_EXCEPTION_OBSERVED = "NO_EXCEPTION_OBSERVED"
    FINDING = "FINDING"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NOT_EVALUATED = "NOT_EVALUATED"


class FactKind(str, Enum):
    PDP = "PDP"
    ENERGYGUIDE = "ENERGYGUIDE"
    EPA = "EPA"


GROUPS = frozenset(
    (
        "refrigerator",
        "dishwasher",
        "washer",
        "tv",
        "range",
        "cooktop",
        "dryer",
        "hood",
        "monitor",
        "computer",
        "tablet",
    )
)
ISSUES = frozenset(
    (
        "ENERGYGUIDE_DOCUMENT_MISSING_CANDIDATE",
        "ENERGYGUIDE_WRONG_DOCUMENT_CANDIDATE",
        "CRITICAL_WRONG_MODEL_LABEL_CANDIDATE",
        "ENERGYGUIDE_OCR_MODEL_CHAR_CORRECTED",
        "ENERGYGUIDE_OCR_MODEL_CHAR_SUSPECT",
        "ENERGYGUIDE_FILE_NOT_READABLE_CANDIDATE",
        "CRITICAL_ENERGY_STAR_ELIGIBILITY_CANDIDATE",
        "SAMSUNG_ENERGY_STAR_SOURCE_CONFLICT",
        "ENERGY_STAR_VARIANT_IDENTITY_REVIEW",
        "ENERGYGUIDE_KWH_NOT_EXTRACTED",
        "ENERGYGUIDE_MODEL_WILDCARD_NOT_EXTRACTED",
    )
)


def require(condition: object, message: str) -> None:
    if not condition:
        raise ContractError(message)


def text(value: object) -> TypeGuard[str]:
    return isinstance(value, str) and bool(value.strip())


def sha(value: object) -> bool:
    return isinstance(value, str) and bool(re.fullmatch(r"[a-f0-9]{64}", value))


def timestamp(value: Any) -> None:
    require(text(value), "Timestamp missing")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ContractError("Invalid timestamp") from error
    require(parsed.utcoffset() is not None, "Timestamp requires timezone")


def record(cls: type[T], data: Any) -> T:
    require(isinstance(data, dict), "Record must be an object")
    require(
        set(data) == {f.name for f in fields(cast(Any, cls))},
        "Missing or unknown " + cls.__name__ + " fields",
    )
    try:
        return cls(**data)
    except (TypeError, ValueError) as error:
        raise ContractError("Invalid " + cls.__name__) from error


@dataclass(frozen=True)
class Observation:
    state: ObservationState
    value: Any
    error: str | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "state", ObservationState(self.state))
        if self.state == ObservationState.VALUE:
            require(
                self.value is not None and self.error is None,
                "Observed value requires non-null value/no error",
            )
        elif self.state == ObservationState.ERROR:
            require(
                self.value is None and text(self.error), "Error observation requires error/no value"
            )
        else:
            require(
                self.value is None and self.error is None,
                "Absent observation cannot contain a value/error",
            )
        json.dumps(self.value, allow_nan=False)


@dataclass(frozen=True)
class RunManifest:
    schema_version: str
    run_id: str
    started_at: str
    completed_at: str | None
    git_sha: str
    config_hash: str
    rule_version: str | None
    source_contract_version: str
    python_version: str
    playwright_version: str | None
    runner: str
    overall_execution_status: PipelineStatus
    assessment_enabled: bool

    def __post_init__(self) -> None:
        require(self.schema_version == "draft-1", "Unsupported draft schema version")
        require(
            text(self.run_id) and text(self.runner) and text(self.source_contract_version),
            "Run identity missing",
        )
        require(
            isinstance(self.git_sha, str) and bool(re.fullmatch(r"[a-f0-9]{40}", self.git_sha)),
            "Invalid git SHA",
        )
        require(sha(self.config_hash), "Invalid config hash")
        require(
            text(self.python_version)
            and (self.playwright_version is None or text(self.playwright_version)),
            "Invalid runtime version",
        )
        require(
            type(self.assessment_enabled) is bool and not self.assessment_enabled,
            "Assessment engine not enabled in Phase 1",
        )
        require(self.rule_version is None, "No approved rule version in this draft")
        object.__setattr__(
            self, "overall_execution_status", PipelineStatus(self.overall_execution_status)
        )
        timestamp(self.started_at)
        if self.completed_at is not None:
            timestamp(self.completed_at)
            require(
                datetime.fromisoformat(self.completed_at.replace("Z", "+00:00"))
                >= datetime.fromisoformat(self.started_at.replace("Z", "+00:00")),
                "Run completion precedes start",
            )


@dataclass(frozen=True)
class ListingProvenance:
    product_group: str
    source_family_id: str
    representative_sku: str
    sku_role: str
    plp_url: str
    pdp_url: str
    source_pf_search_hash: str
    source_family_code: Observation
    commerce_status: Observation
    stock_flag: Observation
    ecom_flag: Observation
    variant_attributes: Observation

    def __post_init__(self) -> None:
        require(
            self.product_group in GROUPS and text(self.source_family_id),
            "Invalid listing group/namespace",
        )
        require(
            text(self.representative_sku) and self.sku_role in ("REPRESENTATIVE", "VARIANT"),
            "Invalid listing role",
        )
        require(
            text(self.plp_url)
            and text(self.pdp_url)
            and self.plp_url.startswith("https://")
            and self.pdp_url.startswith("https://"),
            "Listing URL must be HTTPS",
        )
        require(sha(self.source_pf_search_hash), "Invalid listing source hash")
        for name in (
            "source_family_code",
            "commerce_status",
            "stock_flag",
            "ecom_flag",
            "variant_attributes",
        ):
            value = record(Observation, getattr(self, name))
            if name == "variant_attributes" and value.state == ObservationState.VALUE:
                require(isinstance(value.value, dict), "Variant attributes must be an object")


@dataclass(frozen=True)
class ProductPopulationRecord:
    run_id: str
    exact_sku: str
    listings: list[ListingProvenance]


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    run_id: str
    product_group: str
    sku: str
    source_url: str
    captured_at: str
    sha256: str
    parser_version: str
    evidence_type: str
    relative_path: str

    def __post_init__(self) -> None:
        require(
            all(
                text(x)
                for x in (
                    self.evidence_id,
                    self.run_id,
                    self.sku,
                    self.parser_version,
                    self.evidence_type,
                )
            ),
            "Evidence identity missing",
        )
        require(
            self.product_group in GROUPS
            and text(self.source_url)
            and self.source_url.startswith("https://"),
            "Evidence source invalid",
        )
        require(sha(self.sha256), "Invalid evidence hash")
        timestamp(self.captured_at)
        path = PurePosixPath(self.relative_path)
        require(
            text(self.relative_path)
            and not path.is_absolute()
            and ".." not in path.parts
            and "\\" not in self.relative_path
            and ":" not in self.relative_path,
            "Unsafe evidence path",
        )


@dataclass(frozen=True)
class FactRecord:
    fact_id: str
    run_id: str
    product_group: str
    exact_sku: str
    kind: FactKind
    observations: dict[str, Observation]
    evidence_ids: list[str]


@dataclass(frozen=True)
class AssessmentRecord:
    assessment_id: str
    run_id: str
    product_group: str
    exact_sku: str
    regulatory_domain: str
    control_id: str
    rule_id: str | None
    rule_version: str | None
    assessment_status: AssessmentStatus
    severity: str | None
    issue_code: str | None
    reason: str
    expected: Any
    observed: Any
    evidence_ids: list[str]
    automatic_final_legal_conclusion: bool


def validate_bundle(data: dict[str, Any], *, synthetic_assessments: bool = False) -> dict[str, Any]:
    from .facts import validate_observations

    require(
        isinstance(data, dict)
        and set(data) == {"manifest", "products", "facts", "evidence", "assessments"},
        "Invalid bundle envelope",
    )
    manifest = record(RunManifest, data["manifest"])
    for key in ("products", "facts", "evidence", "assessments"):
        require(isinstance(data[key], list), "Bundle collections must be arrays")
    products: dict[str, set[str]] = {}
    has_errors = False
    for raw in data["products"]:
        product = record(ProductPopulationRecord, raw)
        require(
            product.run_id == manifest.run_id and text(product.exact_sku), "Product run/SKU invalid"
        )
        require(
            product.exact_sku not in products, "Duplicate product key; no implicit deduplication"
        )
        require(
            isinstance(product.listings, list) and product.listings, "Listing provenance missing"
        )
        listings = [record(ListingProvenance, v) for v in product.listings]
        has_errors |= any(
            record(Observation, getattr(v, name)).state == ObservationState.ERROR
            for v in listings
            for name in (
                "source_family_code",
                "commerce_status",
                "stock_flag",
                "ecom_flag",
                "variant_attributes",
            )
        )
        products[product.exact_sku] = {v.product_group for v in listings}
    evidence: dict[str, EvidenceRecord] = {}
    for raw in data["evidence"]:
        item = record(EvidenceRecord, raw)
        require(item.evidence_id not in evidence, "Duplicate evidence ID")
        require(
            item.run_id == manifest.run_id and item.product_group in products.get(item.sku, set()),
            "Evidence run/SKU/group mismatch",
        )
        evidence[item.evidence_id] = item

    def references(item: FactRecord | AssessmentRecord) -> None:
        require(
            item.run_id == manifest.run_id
            and item.product_group in products.get(item.exact_sku, set()),
            "Record run/SKU/group mismatch",
        )
        require(
            isinstance(item.evidence_ids, list)
            and len(item.evidence_ids) == len(set(item.evidence_ids)),
            "Invalid/duplicate evidence references",
        )
        for key in item.evidence_ids:
            require(key in evidence, "Missing evidence reference")
            target = evidence[key]
            require(
                target.run_id == item.run_id
                and target.sku == item.exact_sku
                and target.product_group == item.product_group,
                "Cross-product evidence reference",
            )

    seen = set()
    for raw in data["facts"]:
        fact_item = record(FactRecord, raw)
        references(fact_item)
        require(
            text(fact_item.fact_id) and fact_item.fact_id not in seen, "Invalid/duplicate fact ID"
        )
        seen.add(fact_item.fact_id)
        FactKind(fact_item.kind)
        require(
            isinstance(fact_item.observations, dict) and fact_item.observations,
            "Fact observations missing",
        )
        require(all(text(k) for k in fact_item.observations), "Observation name missing")
        observations = validate_observations(
            fact_item.kind,
            fact_item.observations,
            {evidence[key].sha256 for key in fact_item.evidence_ids},
        )
        has_errors |= any(v.state == ObservationState.ERROR for v in observations)
    seen = set()
    for raw in data["assessments"]:
        assessment_item = record(AssessmentRecord, raw)
        references(assessment_item)
        require(
            text(assessment_item.assessment_id) and assessment_item.assessment_id not in seen,
            "Invalid/duplicate assessment ID",
        )
        seen.add(assessment_item.assessment_id)
        require(
            assessment_item.regulatory_domain in ("FTC", "EPA")
            and text(assessment_item.control_id),
            "Invalid domain/control",
        )
        require(text(assessment_item.reason), "Assessment reason missing")
        require(
            assessment_item.automatic_final_legal_conclusion is False,
            "Automatic legal conclusion prohibited",
        )
        status = AssessmentStatus(assessment_item.assessment_status)
        if not synthetic_assessments:
            require(
                status == AssessmentStatus.NOT_EVALUATED
                and assessment_item.rule_id is None
                and assessment_item.rule_version is None
                and assessment_item.issue_code is None
                and assessment_item.severity is None,
                "Draft CLI cannot accept evaluated assessments",
            )
        elif status == AssessmentStatus.FINDING:
            require(
                assessment_item.issue_code in ISSUES
                and assessment_item.severity in ("HIGH", "MEDIUM", "LOW")
                and assessment_item.evidence_ids,
                "Synthetic finding requires existing issue/severity/evidence",
            )
    if has_errors:
        require(
            manifest.overall_execution_status != PipelineStatus.SUCCESS,
            "Source error cannot become execution SUCCESS",
        )
        require(
            all(a["assessment_status"] == "NOT_EVALUATED" for a in data["assessments"]),
            "Error bundle cannot claim evaluated status in draft",
        )
    json.dumps(data, allow_nan=False)
    return data


def verify_evidence_files(data: dict[str, Any], root: str | Path) -> None:
    """Verify stored raw bytes; reject links escaping the supplied evidence root."""
    root = Path(root).resolve(strict=True)
    for item in data["evidence"]:
        path = (root / item["relative_path"]).resolve(strict=True)
        require(
            path.is_relative_to(root) and path.is_file(), "Evidence escapes root or is not a file"
        )
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(65536), b""):
                digest.update(chunk)
        require(digest.hexdigest() == item["sha256"], "Evidence bytes do not match manifest")


def dumps(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"
