import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from csv_stats import column_stats, compute_stats, format_number, main, parse_number, read_columns


class ParseNumberTest(unittest.TestCase):

    def test_numbers(self):
        self.assertEqual(parse_number("42"), 42.0)
        self.assertEqual(parse_number("-3.5"), -3.5)
        self.assertEqual(parse_number("1e3"), 1000.0)

    def test_non_numbers(self):
        for text in ("abc", "", "nan", "inf"):
            self.assertIsNone(parse_number(text))


class ReadColumnsTest(unittest.TestCase):

    def test_short_rows_and_blank_lines(self):
        headers, columns = read_columns(["a,b", "1,2", "", "3"])
        self.assertEqual(headers, ["a", "b"])
        self.assertEqual(columns, [["1", "3"], ["2", ""]])

    def test_blank_header_gets_name(self):
        headers, _ = read_columns(["a,", "1,2"])
        self.assertEqual(headers, ["a", "column2"])

    def test_empty_input(self):
        self.assertEqual(read_columns([]), ([], []))

    def test_custom_delimiter(self):
        headers, columns = read_columns(["a;b", "1;2"], delimiter=";")
        self.assertEqual(headers, ["a", "b"])
        self.assertEqual(columns, [["1"], ["2"]])


class ColumnStatsTest(unittest.TestCase):

    def test_numeric(self):
        stats = column_stats(["2", "4", "4", "4", "5", "5", "7", "9", ""])
        self.assertEqual(stats["type"], "numeric")
        self.assertEqual(stats["count"], 8)
        self.assertEqual(stats["missing"], 1)
        self.assertEqual(stats["min"], 2)
        self.assertEqual(stats["max"], 9)
        self.assertEqual(stats["mean"], 5)
        self.assertEqual(stats["median"], 4.5)
        self.assertAlmostEqual(stats["stdev"], 2.1380899, places=6)

    def test_single_value_has_no_stdev(self):
        self.assertIsNone(column_stats(["3"])["stdev"])

    def test_text(self):
        stats = column_stats(["red", "blue", "red", " ", "green"])
        self.assertEqual(stats["type"], "text")
        self.assertEqual(stats["count"], 4)
        self.assertEqual(stats["missing"], 1)
        self.assertEqual(stats["unique"], 3)
        self.assertEqual(stats["most_common"], ("red", 2))

    def test_mixed_column_is_text(self):
        self.assertEqual(column_stats(["1", "2", "three"])["type"], "text")

    def test_empty_column(self):
        self.assertEqual(column_stats(["", ""]), {"count": 0, "missing": 2, "type": "empty"})


class FormatTest(unittest.TestCase):

    def test_format_number(self):
        self.assertEqual(format_number(3.0), "3")
        self.assertEqual(format_number(2.123456), "2.1235")
        self.assertEqual(format_number(None), "n/a")


class MainTest(unittest.TestCase):

    def run_main(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_bundled_sample(self):
        sample = Path(__file__).with_name("sample.csv")
        with open(sample, newline="") as handle:
            results = dict(compute_stats(handle))
        self.assertEqual(results["department"]["most_common"], ("Engineering", 4))
        self.assertEqual(results["age"]["median"], 34)
        self.assertEqual(results["salary"]["missing"], 1)

        code, out, _ = self.run_main([str(sample)])
        self.assertEqual(code, 0)
        self.assertIn("salary (numeric)", out)
        self.assertIn("most common Engineering (4)", out)

    def test_delimiter_option(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.csv"
            path.write_text("x;y\n1;a\n3;b\n")
            code, out, _ = self.run_main([str(path), "-d", ";"])
        self.assertEqual(code, 0)
        self.assertIn("x (numeric)", out)
        self.assertIn("mean        2", out)

    def test_missing_file(self):
        code, _, err = self.run_main(["does-not-exist.csv"])
        self.assertEqual(code, 1)
        self.assertIn("Error", err)


if __name__ == "__main__":
    unittest.main()
