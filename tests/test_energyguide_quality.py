import unittest
from scripts.energyguide_quality import model_regions, project_detections, observation


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
