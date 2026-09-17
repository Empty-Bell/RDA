import hashlib
import tempfile
import unittest
from pathlib import Path
from scripts.runtime_integrity import inspect_files,require_integrity,safe_path


class RuntimeIntegrity(unittest.TestCase):
    def test_missing_and_changed_resources_block_without_replacing_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);path=root/'model.onnx';original=b'CONTROLLED_FIXTURE'
            record={'path':'model.onnx','sha256':hashlib.sha256(original).hexdigest()}
            with self.assertRaises(ValueError):require_integrity(inspect_files(root,[record]))
            path.write_bytes(original);require_integrity(inspect_files(root,[record]))
            path.write_bytes(original+b'CORRUPTED')
            observed=inspect_files(root,[record])
            with self.assertRaises(ValueError):require_integrity(observed)
            self.assertNotEqual(observed[0]['expected_sha256'],observed[0]['actual_sha256'])
            self.assertEqual(path.read_bytes(),original+b'CORRUPTED')

    def test_path_traversal_absolute_path_and_duplicate_records_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for relative in ('../model.onnx',str(root/'model.onnx')):
                with self.assertRaises(ValueError):safe_path(root,relative)
            r={'path':'model.onnx','sha256':'a'*64}
            with self.assertRaises(ValueError):inspect_files(root,[r,r])

    def test_empty_manifest_or_missing_hash_never_passes(self):
        with self.assertRaises(ValueError):require_integrity([])
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):inspect_files(Path(directory),[{'path':'model.onnx','sha256':'missing'}])
