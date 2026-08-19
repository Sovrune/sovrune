import tempfile
import unittest
from pathlib import Path

from sovrune.sdk import AdapterError, load_adapter, scaffold_company, validate_adapter


class AdapterSdkTest(unittest.TestCase):
    def test_default_adapter_validates(self):
        report = validate_adapter()
        self.assertEqual(report.company, "Acme Solar")
        self.assertGreater(report.metrics, 1)

    def test_scaffold_is_immediately_valid(self):
        with tempfile.TemporaryDirectory() as directory:
            target, class_name = scaffold_company("North Star Labs", directory, "anthropic")
            reference = f"{target / 'adapter.py'}:{class_name}"
            report = validate_adapter(reference)
            self.assertEqual(report.company, "North Star Labs")
            self.assertIn("SOVRUNE_PROVIDER=anthropic", (target / ".env.example").read_text())
            self.assertNotIn("API_KEY=", (target / ".env.example").read_text())

    def test_non_adapter_class_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.py"
            path.write_text("class NotAnAdapter: pass\n")
            with self.assertRaises(AdapterError):
                load_adapter(f"{path}:NotAnAdapter")

    def test_nonempty_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "keep.txt").write_text("mine")
            with self.assertRaises(AdapterError):
                scaffold_company("Example", directory)


if __name__ == "__main__":
    unittest.main()
