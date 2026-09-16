"""Bounded degradation/ROI observations; no OCR correction or audit decisions."""
import argparse
import hashlib
import json
from pathlib import Path

try:
    from .energyguide_fields import label_candidates, annual_layout_candidates
except ImportError:
    from energyguide_fields import label_candidates, annual_layout_candidates


def rectangle(box):
    if len(box) == 4 and isinstance(box[0], (int, float)):
        return list(box)
    return [min(p[0] for p in box), min(p[1] for p in box),
            max(p[0] for p in box), max(p[1] for p in box)]


def model_regions(spans, page_rect, digest):
    regions = []
    for index, span in enumerate(spans):
        if span['page'] != 0:
            continue
        candidates = label_candidates(span['text'], span['engine'], digest)['model_candidates_raw']
        if not candidates:
            continue
        box = rectangle(span['bbox'])
        padding = max(box[3] - box[1], 1)
        clip = [max(page_rect[0], box[0] - padding), max(page_rect[1], box[1] - padding),
                min(page_rect[2], box[2] + padding), min(page_rect[3], box[3] + padding)]
        regions.append({'source_detection': index, 'source_text_raw': span['text'],
                        'model_candidates_raw': candidates, 'clip_pdf_points': clip})
    if len(regions) > 8:
        raise ValueError('Model-like ROI bound exceeded; no silent truncation')
    return regions


def project_detections(texts, boxes, scores, scale, origin):
    if not (len(texts) == len(boxes) == len(scores)):
        raise ValueError('OCR detection arrays disagree')
    return [{'page': 0, 'text': str(text),
             'bbox': [[float(p[0]) / scale + origin[0], float(p[1]) / scale + origin[1]] for p in box],
             'confidence': float(score), 'engine': 'RapidOCR'}
            for text, box, score in zip(texts, boxes, scores)]


def observation(spans, digest):
    text = '\n'.join(s['text'] for s in spans)
    fields = label_candidates(text, 'RapidOCR', digest) if text.strip() else None
    return {'ocr_detection_count': len(spans), 'fields_raw': fields,
            'layout_raw': annual_layout_candidates(spans, digest),
            'text_observation': 'TEXT_OBSERVED' if text.strip() else 'NO_TEXT_OBSERVED',
            'annual_value_selection': 'NOT_EVALUATED', 'wildcard_correction': 'NOT_APPLIED',
            'identity_matching': 'NOT_EVALUATED', 'compliance': 'NOT_EVALUATED'}


def compare_model_candidates(baseline_candidates, observed):
    baseline = [c['value_raw'] for c in baseline_candidates]
    fields = observed['fields_raw']
    current = [c['value_raw'] for c in fields['model_candidates_raw']] if fields else []
    return {'baseline_candidates_raw': baseline, 'observed_candidates_raw': current,
            'raw_set_observation': 'SAME_RAW_CANDIDATE_SET' if set(baseline) == set(current) else 'DIFFERENT_RAW_CANDIDATE_SET',
            'wildcard_correction': 'NOT_APPLIED', 'identity_matching': 'NOT_EVALUATED'}


def probe(root, engine):
    import pymupdf
    output = root / 'quality'
    output.mkdir(exist_ok=True)
    def save(name, data):
        (output / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    summary = {'status': 'RUNNING', 'scope': 'page 1 degradation and model-like ROI only',
               'variants': [], 'wildcard_correction': 'NOT_APPLIED',
               'identity_matching': 'NOT_EVALUATED', 'compliance': 'NOT_EVALUATED'}
    save('summary.json', summary)
    try:
        raw = (root / 'energyguide-original.pdf').read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        source = json.loads((root / 'energyguide-observation.json').read_text(encoding='utf-8'))
        assert digest == source['sha256'], 'Quality input PDF hash differs'
        summary['pdf_sha256'] = digest
        spans_file = root / 'fixtures' / ('energyguide-ocr-spans.json' if source['extraction_engine'] == 'RapidOCR' else 'energyguide-embedded-spans.json')
        baseline = json.loads(spans_file.read_text(encoding='utf-8'))
        baseline_models = label_candidates('\n'.join(s['text'] for s in baseline), source['extraction_engine'], digest)['model_candidates_raw']
        with pymupdf.open(stream=raw, filetype='pdf') as doc:
            page = doc[0]
            regions = model_regions(baseline, list(page.rect), digest)
            summary['model_regions_raw'] = regions
            save('model-regions.json', regions)
            variants = [('page-36dpi', 0.5, None), ('page-72dpi', 1, None)]
            variants += [('model-roi-' + str(i), 3, r['clip_pdf_points']) for i, r in enumerate(regions)]
            for name, scale, clip in variants:
                pix = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), clip=pymupdf.Rect(clip) if clip else None)
                image = output / (name + '.png')
                pix.save(image)
                provenance = {'name': name, 'pdf_sha256': digest, 'page': 0, 'scale': scale,
                              'dpi': scale * 72, 'clip_pdf_points': clip,
                              'pixel_origin': [pix.x, pix.y], 'pixel_size': [pix.width, pix.height],
                              'png_sha256': hashlib.sha256(image.read_bytes()).hexdigest(),
                              'transformation': 'PDF render at stated scale; no glyph correction'}
                save(name + '-render.json', provenance)
                result = engine(str(image))
                texts = [] if result.txts is None else list(result.txts)
                boxes = [] if result.boxes is None else list(result.boxes)
                scores = [] if result.scores is None else list(result.scores)
                # Preserve OCR outputs before candidate parsing and geometry projection.
                save(name + '-raw.json', {'texts': texts, 'boxes_pixels': [b.tolist() if hasattr(b, 'tolist') else b for b in boxes],
                                          'scores': [float(s) for s in scores]})
                spans = project_detections(texts, boxes, scores, scale, [pix.x / scale, pix.y / scale])
                save(name + '-spans.json', spans)
                observed = observation(spans, digest)
                reference = regions[int(name.rsplit('-', 1)[1])]['model_candidates_raw'] if clip else baseline_models
                observed['model_candidate_comparison'] = compare_model_candidates(reference, observed)
                save(name + '-observation.json', observed)
                summary['variants'].append({'render': provenance, 'observation': observed})
                save('summary.json', summary)
        summary['status'] = 'PASS'
        summary['status_meaning'] = 'probe completed and evidence preserved; readability/identity never PASS'
        summary['source_model_region_observation'] = 'CANDIDATES_OBSERVED' if regions else 'NOT_OBSERVED'
        save('summary.json', summary)
    except Exception as error:
        summary['status'] = 'FAIL'
        summary['error'] = {'type': type(error).__name__, 'message': str(error)}
        save('summary.json', summary)
        raise
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--family', required=True, choices=['refrigerator', 'dishwasher', 'washer', 'tv'])
    args = parser.parse_args()
    from rapidocr import RapidOCR
    engine = RapidOCR(params={'EngineConfig.onnxruntime.intra_op_num_threads': 1,
                              'EngineConfig.onnxruntime.inter_op_num_threads': 1})
    root = Path('runtime/source-recon') / args.family
    roots = [root] + sorted(p.parent for p in root.glob('*/energyguide-original.pdf'))
    for item in roots:
        summary = probe(item, engine)
        print(json.dumps({'label': str(item), 'status': summary['status'], 'variants': len(summary['variants'])}))


if __name__ == '__main__':
    main()
