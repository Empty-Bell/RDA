import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import g3_computer_collect as computer


class ComputerCollectRetryTest(unittest.TestCase):
    def test_retries_only_failed_sku_and_promotes_exact_verified_capture(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            failed_sku = "NP760XJG-KG2US"
            successful_sku = "NP740VJG-KG2US"
            original = root / "pdp" / failed_sku
            original.mkdir(parents=True)
            (original / "result.json").write_text('{"status":"FAILED"}')
            products = [{"exact_sku": failed_sku}, {"exact_sku": successful_sku}]
            rows = [{"exact_sku": failed_sku, "status": "FAILED"},
                    {"exact_sku": successful_sku, "status": "VERIFIED_EXACT_IDENTITY"}]
            called = []

            def recovered_capture(selected, destination):
                called.append([row["exact_sku"] for row in selected])
                folder = Path(destination) / "pdp" / failed_sku
                folder.mkdir(parents=True)
                for name in ("result.json", "snapshot.json", "specs.json"):
                    (folder / name).write_text(json.dumps({"exact_sku": failed_sku, "name": name}))
                return [{"exact_sku": failed_sku, "status": "VERIFIED_EXACT_IDENTITY"}]

            with patch.object(computer, "collect", recovered_capture):
                result = computer.retry_failed(products, rows, root)
            self.assertEqual(called, [[failed_sku]])
            self.assertEqual([row["status"] for row in result],
                             ["VERIFIED_EXACT_IDENTITY", "VERIFIED_EXACT_IDENTITY"])
            for name in ("result.json", "snapshot.json", "specs.json"):
                self.assertEqual(json.loads((original / name).read_text())["exact_sku"], failed_sku)


if __name__ == "__main__":
    unittest.main()
