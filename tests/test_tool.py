import contextlib
import io
from pathlib import Path
import tempfile
import unittest
import rowwidthbeacon as tool


class CsvChecks(unittest.TestCase):
    def run_text(self, text, **kwargs):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "输入.csv"
            path.write_text(text, encoding="utf-8-sig", newline="")
            before = path.read_bytes()
            report = tool.inspect_csv(path, **kwargs)
            self.assertEqual(path.read_bytes(), before)
            return report

    def test_width_and_real_blank_limit(self):
        text = "a,b\nx,\ny, \nz\n"
        report = self.run_text(text, blank_limit=2)
        self.assertEqual((report["data_records"], report["matching_width_records"], report["width_mismatch_count"]), (3, 2, 1))
        self.assertEqual(report["columns"][1]["blank_cells"], 2)
        self.assertTrue(report["columns"][1]["alert"])
        self.assertFalse(self.run_text(text, blank_limit=3)["columns"][1]["alert"])

    def test_quotes_newlines_and_locations(self):
        report = self.run_text('a,b\r\n"first\r\nsecond","x,y"\r\nz\r\n')
        self.assertEqual(report["matching_width_records"], 1)
        self.assertEqual(report["width_mismatches"][0], {"record": 3, "start_line": 4, "end_line": 4, "actual_columns": 1})

    def test_header_and_blank_record(self):
        report = self.run_text("a,a, \n\nx,y,z\n")
        self.assertEqual(report["duplicate_headers"], ["a"])
        self.assertEqual(report["blank_header_positions"], [3])
        self.assertEqual(report["width_mismatches"][0]["actual_columns"], 0)

    def test_detail_limit_keeps_total(self):
        report = self.run_text("a,b\nx\ny\nz\n", max_details=1)
        self.assertEqual(report["width_mismatch_count"], 3)
        self.assertEqual(len(report["width_mismatches"]), 1)
        self.assertTrue(report["details_truncated"])

    def test_clean_semicolon(self):
        self.assertFalse(self.run_text("姓名;年龄\n小王;20\n", delimiter=";")["has_findings"])

    def test_errors_and_exit_codes(self):
        with self.assertRaises(ValueError):
            self.run_text("")
        with self.assertRaises(ValueError):
            self.run_text("a\nx\n", blank_limit=0)
        with self.assertRaises(ValueError):
            self.run_text("a\nx\n", delimiter="ab")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "data.csv"
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                path.write_text("a\nx\n", encoding="utf-8")
                self.assertEqual(tool.main([str(path)]), 0)
                path.write_text("a\n \n", encoding="utf-8")
                self.assertEqual(tool.main([str(path)]), 1)
                path.write_text('a,b\n"unclosed', encoding="utf-8")
                self.assertEqual(tool.main([str(path)]), 2)
                self.assertEqual(tool.main([str(path), "--encoding", "missing-encoding"]), 2)


if __name__ == "__main__":
    unittest.main()
