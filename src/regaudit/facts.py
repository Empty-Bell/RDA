"""Typed source observations. No conversion, matching or compliance rules."""
from dataclasses import dataclass, fields
import math
from .contracts import Observation, ObservationState, record, require, sha, text, timestamp


@dataclass(frozen=True)
class PdpFactRecord:
    pdp_model: Observation
    pdp_url: Observation
    product_title: Observation
    pdp_annual_energy_kwh: Observation
    pdp_capacity: Observation
    energyguide_url: Observation
    plp_energy_star_claim: Observation
    pdp_structured_energy_star_claim: Observation
    pdp_spec_energy_star_claim: Observation
    source_bridge_hash: Observation


@dataclass(frozen=True)
class EnergyGuideExtractionRecord:
    document_url: Observation
    document_sha256: Observation
    document_status: Observation
    extraction_engine: Observation
    embedded_text: Observation
    ocr_raw_text: Observation
    label_model_raw: Observation
    label_model_normalized: Observation
    annual_energy_kwh: Observation
    capacity: Observation
    model_confusion_detected: Observation
    model_confusion_corrected: Observation
    correction_reason: Observation
    fallback_reason: Observation
    ocr_scale: Observation
    ocr_roi_used: Observation


@dataclass(frozen=True)
class EpaRecord:
    dataset_id: Observation
    epa_unique_id: Observation
    model_number: Observation
    upc: Observation
    annual_energy_kwh: Observation
    markets: Observation
    certification_status: Observation
    retrieved_at: Observation
    source_hash: Observation


TYPES = {'PDP': PdpFactRecord, 'ENERGYGUIDE': EnergyGuideExtractionRecord, 'EPA': EpaRecord}
BOOLEAN_FIELDS = {'plp_energy_star_claim','pdp_structured_energy_star_claim',
                  'pdp_spec_energy_star_claim','model_confusion_detected','model_confusion_corrected'}
HASH_FIELDS = {'source_bridge_hash','document_sha256','source_hash'}
URL_FIELDS = {'pdp_url','energyguide_url','document_url'}
MEASUREMENTS = {'pdp_annual_energy_kwh','annual_energy_kwh','pdp_capacity','capacity'}


def validate_observations(kind, data, evidence_hashes):
    cls = TYPES[kind]
    typed = record(cls, data)
    observations = []
    for field in fields(cls):
        name = field.name
        observed = record(Observation, getattr(typed, name))
        observations.append(observed)
        if observed.state != ObservationState.VALUE: continue
        value = observed.value
        if name in BOOLEAN_FIELDS:
            require(type(value) is bool, 'Claim/confusion flag must be a boolean')
        elif name in HASH_FIELDS:
            require(sha(value) and value in evidence_hashes, 'Source hash must reference stored evidence')
        elif name in URL_FIELDS:
            require(text(value) and value.startswith('https://'), 'Source URL must be HTTPS')
        elif name in MEASUREMENTS:
            require(isinstance(value, dict) and set(value) == {'amount','unit','raw'}, 'Measurement requires amount/unit/raw')
            require(type(value['amount']) in (int,float) and math.isfinite(value['amount']), 'Measurement must be finite numeric, not boolean')
            require(text(value['unit']) and text(value['raw']), 'Measurement unit/raw missing')
            if name.endswith('energy_kwh'):
                require(value['unit'] == 'kWh/year', 'Annual energy requires explicit kWh/year; no implicit conversion')
        elif name == 'markets':
            require(isinstance(value, list) and all(text(v) for v in value), 'Markets must preserve source strings')
        elif name == 'retrieved_at': timestamp(value)
        elif name == 'ocr_scale':
            require(type(value) in (int,float) and math.isfinite(value) and value > 0, 'Invalid OCR scale')
        elif name == 'ocr_roi_used':
            require(isinstance(value, dict) and set(value) == {'page','box','coordinate_unit'}, 'ROI requires page/box/coordinate_unit')
            require(type(value['page']) is int and value['page'] >= 0, 'Invalid zero-based ROI page')
            box = value['box']
            require(isinstance(box,list) and len(box)==4 and all(type(v) in (int,float) and math.isfinite(v) for v in box), 'Invalid ROI coordinates')
            require(box[0] < box[2] and box[1] < box[3] and text(value['coordinate_unit']), 'Invalid ROI extent/unit')
        else:
            require(isinstance(value,str), 'Text observation must preserve a source string')
            if name not in {'embedded_text','ocr_raw_text'}: require(text(value), 'Empty identity/text field')
    require(not any(o.state == ObservationState.VALUE for o in observations) or evidence_hashes, 'Observed facts require raw evidence')
    return observations
