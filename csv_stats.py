#!/usr/bin/env python3
"""Print per-column summary statistics for a CSV file."""

import argparse
import csv
import math
import statistics
import sys
from collections import Counter


def parse_number(text):
    """Return text as a finite float, or None if it is not a number."""
    try:
        value = float(text)
    except ValueError:
        return None
    return value if math.isfinite(value) else None


def read_columns(lines, delimiter=","):
    """Read CSV lines into (headers, columns) where columns[i] is a list of raw strings.

    Short rows count as missing values; extra cells beyond the header are ignored.
    """
    reader = csv.reader(lines, delimiter=delimiter)
    header = next(reader, None)
    if header is None:
        return [], []
    headers = [name.strip() or f"column{i + 1}" for i, name in enumerate(header)]
    columns = [[] for _ in headers]
    for row in reader:
        if not any(cell.strip() for cell in row):
            continue  # skip blank lines
        for i, column in enumerate(columns):
            column.append(row[i] if i < len(row) else "")
    return headers, columns


def column_stats(values):
    """Summarize one column. Numeric if every non-empty value is a number."""
    present = [value.strip() for value in values if value.strip()]
    stats = {"count": len(present), "missing": len(values) - len(present)}
    if not present:
        stats["type"] = "empty"
        return stats

    numbers = [parse_number(value) for value in present]
    if all(number is not None for number in numbers):
        stats.update(
            type="numeric",
            min=min(numbers),
            max=max(numbers),
            mean=statistics.fmean(numbers),
            median=statistics.median(numbers),
            stdev=statistics.stdev(numbers) if len(numbers) > 1 else None,
        )
    else:
        counts = Counter(present)
        value, count = counts.most_common(1)[0]
        stats.update(type="text", unique=len(counts), most_common=(value, count))
    return stats


def compute_stats(lines, delimiter=","):
    """Return a list of (column name, stats dict) for every column."""
    headers, columns = read_columns(lines, delimiter)
    return [(name, column_stats(values)) for name, values in zip(headers, columns)]


def format_number(value):
    if value is None:
        return "n/a"
    rounded = round(value, 4)
    return str(int(rounded)) if rounded.is_integer() else str(rounded)


def format_report(results):
    """Turn compute_stats() output into a readable text report."""
    blocks = []
    for name, stats in results:
        rows = [("count", stats["count"]), ("missing", stats["missing"])]
        if stats["type"] == "numeric":
            rows += [(key, format_number(stats[key])) for key in ("min", "max", "mean", "median", "stdev")]
        elif stats["type"] == "text":
            value, count = stats["most_common"]
            rows += [("unique", stats["unique"]), ("most common", f"{value} ({count})")]
        lines = [f"{name} ({stats['type']})"]
        lines += [f"  {label:<12}{value}" for label, value in rows]
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Print per-column statistics for a CSV file.")
    parser.add_argument("csv_file", help="path to the CSV file, or - to read from stdin")
    parser.add_argument("-d", "--delimiter", default=",", help="field delimiter (default: ,)")
    args = parser.parse_args(argv)

    if len(args.delimiter) != 1:
        parser.error("delimiter must be a single character")

    try:
        if args.csv_file == "-":
            results = compute_stats(sys.stdin, args.delimiter)
        else:
            with open(args.csv_file, newline="", encoding="utf-8") as handle:
                results = compute_stats(handle, args.delimiter)
    except (OSError, UnicodeDecodeError, csv.Error) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if not results:
        print("No columns found.")
        return 0

    print(format_report(results))
    return 0


if __name__ == "__main__":
    sys.exit(main())
