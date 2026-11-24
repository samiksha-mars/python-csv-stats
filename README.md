# Python CSV Stats

A small command-line tool that prints summary statistics for every column of a CSV file.
Uses only the Python standard library.

## Features

- Detects column types automatically: a column is numeric when every non-empty value is a number
- Numeric columns: count, missing, min, max, mean, median, standard deviation
- Text columns: count, missing, number of unique values, most common value
- Blank cells and short rows are counted as missing
- Custom delimiter (`-d ';'`) and reading from stdin (`-`)

## Usage

```bash
python3 csv_stats.py sample.csv

# Semicolon-separated file
python3 csv_stats.py data.csv -d ';'

# Read from stdin
cat sample.csv | python3 csv_stats.py -
```

Example output (excerpt) for the bundled `sample.csv`:

```
department (text)
  count       8
  missing     0
  unique      3
  most common Engineering (4)

salary (numeric)
  count       7
  missing     1
  min         54000
  max         105000
  mean        75285.7143
  median      64000
  stdev       20475.3045
```

## Tests

```bash
python3 -m unittest
```
