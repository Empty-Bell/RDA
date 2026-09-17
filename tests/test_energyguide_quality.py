import unittest
import json
import hashlib
import importlib.util
import tempfile
from pathlib import Path
from scripts.energyguide_quality import model_regions, project_detections, observation, compare_model_candidates, otsu_image


class QualityContract(unittest.TestCase):
    def test_roi_clamps_to_page_preserving_wildcards_and_detection(self):
        span = {'page': 0, 'bbox': [[1, 2], [30, 2], [30, 10], [1, 10]],
                'text': 'Models DW90F8**0***', 'engine': 'RapidOCR'}
        region = model_regions([span], [0, 0, 35, 15], 'a' * 64)[0]
        self.assertEqual(region['clip_pdf_points'], [0, 0, 35, 15])
        self.assertEqual(region['source_detection'], 0)
        self.assertEqual(region['model_candidates_raw'][0]['value_raw'], 'DW90F8**0***')

    def test_crop_pixel_origin_is_restored_in_pdf_coordinates(self):
        spans = project_detections(['RF29DB9900**'], [[[0, 0], [30, 0], [30, 9], [0, 9]]], [.8], 3, [100, 20])
        self.assertEqual(spans[0]['bbox'], [[100, 20], [110, 20], [110, 23], [100, 23]])
        self.assertEqual(spans[0]['confidence'], .8)

    def test_malformed_ocr_arrays_fail_instead_of_silent_zip_truncation(self):
        with self.assertRaises(ValueError):
            project_detections(['model'], [], [], 3, [0, 0])

    def test_empty_degraded_ocr_is_unknown_not_certification_or_readability_pass(self):
        result = observation([], 'a' * 64)
        self.assertEqual(result['text_observation'], 'NO_TEXT_OBSERVED')
        self.assertIsNone(result['fields_raw'])
        self.assertEqual(result['compliance'], 'NOT_EVALUATED')

    def test_roi_candidate_bound_never_silently_truncates(self):
        span = {'page': 0, 'bbox': [10, 10, 50, 20], 'text': 'Models WF90F53*D*', 'engine': 'RapidOCR'}
        with self.assertRaises(ValueError):
            model_regions([span] * 9, [0, 0, 100, 100], 'a' * 64)


class ActualQualityRegression(unittest.TestCase):
    @unittest.skipUnless(importlib.util.find_spec('cv2'), 'Hosted bootstrap provides OpenCV')
    def test_actual_repeated_wildcard_roi_binarization_preserves_source_and_dimensions(self):
        import cv2
        source = Path(__file__).parent / 'fixtures/energyguide-quality/images/dishwasher-model-roi.png'
        before = source.read_bytes()
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / 'otsu.png'
            metadata = otsu_image(source, destination)
            binary = cv2.imread(str(destination), cv2.IMREAD_GRAYSCALE)
            self.assertEqual(binary.shape, cv2.imread(str(source), cv2.IMREAD_GRAYSCALE).shape)
            self.assertEqual(set(int(v) for v in binary.ravel()), {0, 255})
            self.assertEqual(metadata['source_png_sha256'], hashlib.sha256(before).hexdigest())
            self.assertEqual(source.read_bytes(), before)

    def fixture(self, name):
        return json.loads((Path(__file__).parent / 'fixtures/energyguide-quality' / (name + '.json')).read_text(encoding='utf-8'))

    def variant(self, data, name):
        return next(v for v in data['variants'] if v['render']['name'] == name)

    def models(self, data, name):
        v = self.variant(data, name)
        result = observation(v['spans'], data['pdf_sha256'])
        return [c['value_raw'] for c in result['fields_raw']['model_candidates_raw']]

    def test_actual_36dpi_model_loss_and_digit_confusion_are_not_corrected(self):
        data = self.fixture('refrigerator')
        v = self.variant(data, 'page-36dpi')
        observed = observation(v['spans'], data['pdf_sha256'])
        self.assertEqual(self.models(data, 'page-36dpi'), ['RF290B9900'])
        comparison = compare_model_candidates(data['baseline_model_candidates_raw'], observed)
        self.assertEqual(comparison['raw_set_observation'], 'DIFFERENT_RAW_CANDIDATE_SET')
        self.assertEqual(comparison['identity_matching'], 'NOT_EVALUATED')
        self.assertEqual(comparison['wildcard_correction'], 'NOT_APPLIED')

    def test_actual_72dpi_bilingual_wildcard_disagreement_is_preserved(self):
        data = self.fixture('dishwasher')
        models = self.models(data, 'page-72dpi')
        self.assertIn('DW90F8**0**', models)
        self.assertIn('DW90F8**0***', models)
        self.assertEqual(self.models(data, 'model-roi-0'), ['DW90F8**0***'])
        self.assertEqual(self.models(data, 'model-roi-1'), ['DW90F8**0***'])

    def test_actual_36dpi_missing_annual_caption_never_becomes_selected_value(self):
        for name in ('refrigerator', 'dishwasher', 'washer', 'washer-standalone', 'tv'):
            data = self.fixture(name)
            observed = observation(self.variant(data, 'page-36dpi')['spans'], data['pdf_sha256'])
            self.assertEqual(observed['layout_raw']['annual_layout_candidates'], [], msg=name)
            self.assertEqual(observed['annual_value_selection'], 'NOT_EVALUATED')
            self.assertEqual(observed['compliance'], 'NOT_EVALUATED')

    def test_actual_roi_part_number_stays_candidate_not_proven_model(self):
        data = self.fixture('washer')
        self.assertIn('DC58-04582A-00', self.models(data, 'page-72dpi'))
        self.assertEqual(self.models(data, 'model-roi-1'), ['DC68-04592A-00'])
        observed = observation(self.variant(data, 'model-roi-1')['spans'], data['pdf_sha256'])
        self.assertEqual(observed['identity_matching'], 'NOT_EVALUATED')

    def test_actual_roi_geometry_retains_source_pdf_and_crop_origin(self):
        data = self.fixture('dishwasher')
        variant = self.variant(data, 'model-roi-0')
        render = variant['render']
        self.assertEqual(render['pdf_sha256'], data['pdf_sha256'])
        self.assertEqual(render['scale'], 3)
        origin = [v / 3 for v in render['pixel_origin']]
        for span in variant['spans']:
            for point in span['bbox']:
                self.assertGreaterEqual(point[0], origin[0])
                self.assertGreaterEqual(point[1], origin[1])
