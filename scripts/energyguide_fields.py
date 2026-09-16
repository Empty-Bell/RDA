"""Raw label candidates with context/provenance; no matching or compliance rules."""
import re

ANNUAL = re.compile(r'estimated\s+yearly\s+electricity|yearly\s+electricity\s+use', re.I)
ENERGY = re.compile(r'(?<![\w.])(?P<value>\d+(?:[.,]\d+)?)\s*kwh\b', re.I)


def label_candidates(text, engine, pdf_sha256):
    if not isinstance(text, str) or not text.strip():
        raise ValueError('Label extraction text unavailable')
    if not re.fullmatch(r'[0-9a-f]{64}', pdf_sha256):
        raise ValueError('Label candidate PDF provenance missing')
    lines = text.splitlines()
    standalone = [{'value_raw':line.strip(),'line':index} for index,line in enumerate(lines)
                  if re.fullmatch(r'\s*\d+(?:[.,]\d+)?\s*',line)]
    captions = [{'text_raw':line,'line':index} for index,line in enumerate(lines) if ANNUAL.search(line)]
    # OCR splits a number and its kWh unit across detections. Join only adjacent
    # standalone numeric/unit lines; preserve both original line indices.
    energy = []
    for index, line in enumerate(lines):
        combined = line
        end = index
        association = 'SAME_TEXT_SPAN'
        if re.fullmatch(r'\s*\d+(?:[.,]\d+)?\s*', line):
            unit_lines = [j for j in range(index + 1,min(len(lines),index+5))
                          if re.fullmatch(r'\s*kwh\s*',lines[j],re.I)]
            if unit_lines:
                end = unit_lines[0]
                combined += ' ' + lines[end]
                association = 'ADJACENT_LINE_PAIR' if end==index+1 else 'NEARBY_ORDER_CANDIDATE'
        for match in ENERGY.finditer(combined):
            context = lines[max(0,index-3):min(len(lines),end+5)]
            annual = any(ANNUAL.search(part) for part in context)
            reference = any(re.search(r'uses least|uses most|consomme le moins|consomme le plus', part, re.I) for part in context)
            role = 'ANNUAL_CAPTION_CONTEXT' if annual and not reference else 'REFERENCE_CONTEXT' if reference and not annual else 'AMBIGUOUS_CONTEXT' if annual and reference else 'UNCLASSIFIED'
            energy.append({'value_raw':match['value'],'unit_raw':'kWh','role':role,
                           'line_start':index,'line_end':end,'matched_text':match[0],
                           'unit_association':association,
                           'context_raw':context})
    models = []
    capacities = []
    for index,line in enumerate(lines):
        for match in re.finditer(r'\b[A-Z]{1,5}\d[A-Z0-9*?/-]{5,}(?![A-Z0-9*?/-])', line):
            models.append({'value_raw':match[0],'line':index,'context_raw':line,
                           'wildcard_count_status':'NOT_EVALUATED' if '*' in match[0] or '?' in match[0] else 'NO_WILDCARD_OBSERVED'})
        if re.search(r'capacity|cubic feet|cu\.?\s*ft',line,re.I):
            capacities.append({'value_raw':line,'line':index})
    return {'pdf_sha256':pdf_sha256,'extraction_engine':engine,
            'energy_candidates_raw':energy,'model_candidates_raw':models,
            'capacity_candidates_raw':capacities,
            'standalone_numeric_candidates_raw':standalone,'annual_caption_lines_raw':captions,
            'annual_value_selection':'NOT_EVALUATED','identity_matching':'NOT_EVALUATED',
            'wildcard_correction':'NOT_APPLIED','compliance':'NOT_EVALUATED'}
