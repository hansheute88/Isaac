"""Checks that G1 AST scanner reports candidates, not verified reachability."""
import tempfile
import unittest
from pathlib import Path
from scripts.g1_execution_surface_inventory import scan


class TestG1InventoryTool(unittest.TestCase):
    def test_collects_effect_and_guard_without_executing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "sample.py").write_text(
                "import os\n"
                "def run():\n"
                "    _check_required_capabilities()\n"
                "    os.system('true')\n",
                encoding="utf-8",
            )
            result = scan(root)
            self.assertEqual(result["files_scanned"], 1)
            self.assertEqual(result["parse_errors"], [])
            self.assertFalse(result["complete_call_graph"])
            self.assertTrue(any(
                entry["callee"] == "os.system"
                for entry in result["call_candidates"]
            ))
            self.assertTrue(any(
                entry["kind"] == "guard_reference"
                for entry in result["call_candidates"]
            ))

    def test_parse_errors_are_reported_not_hidden(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "bad.py").write_text("def broken(:\n", encoding="utf-8")
            result = scan(root)
            self.assertEqual(result["files_scanned"], 1)
            self.assertEqual(result["parsed_files"], 0)
            self.assertEqual(len(result["parse_errors"]), 1)


if __name__ == "__main__":
    unittest.main()
