import unittest
from scripts.runner_probe import safe_url, sanitize, valid_pdf


class ProbeGuardrails(unittest.TestCase):
    def test_public_query_preserved_sensitive_removed(self):
        self.assertEqual(safe_url('https://example.org/api?startIndex=2&token=secret#fragment'),
                         'https://example.org/api?startIndex=2')

    def test_nested_sensitive_data_removed(self):
        self.assertEqual(sanitize({'products': [{'sku': 'TEST', 'email': 'private'}], 'cookie': 'x'}),
                         {'products': [{'sku': 'TEST'}]})

    def test_http_200_html_is_not_pdf(self):
        self.assertFalse(valid_pdf(b'<html>Access denied</html>'))
        self.assertFalse(valid_pdf(b''))
        self.assertTrue(valid_pdf(b'%PDF-1.7 synthetic'))
