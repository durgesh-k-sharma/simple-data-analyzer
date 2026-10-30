# Simple Data Analyzer

A small command-line CSV analyzer built with pandas and matplotlib. It is the
script from freeCodeCamp's
[How to Build a Simple Data Analyzer in Python with Pandas](https://www.freecodecamp.org/news/how-to-build-a-simple-data-analyzer-in-python-with-pandas/),
turned into a tested, installable tool: it loads a CSV, explores it, calculates
statistics, filters and groups rows, plots two charts, and exports results.

With no arguments it analyzes the tutorial's 12-student sample dataset, so you
can see it work before pointing it at your own file.

## Quick start

You need [uv](https://docs.astral.sh/uv/). It installs Python 3.11 or newer for
you if needed.

```bash
uv sync                # create the virtual environment and install dependencies
uv run analyzer        # analyze the bundled sample dataset
```

That prints the full report and saves two charts to `output/`:

- `output/study_hours_vs_score.png`
- `output/average_score_by_grade.png`

Run the tests with `uv run pytest`.

## Using your own data

```bash
uv run analyzer --file my_data.csv
uv run analyzer --file students.csv --min-score 95 --export-dir results
uv run analyzer --file messy.csv --missing drop --no-plots
```

### Options

| Option | Default | What it does |
| --- | --- | --- |
| `--file PATH` | bundled sample | CSV file to analyze. |
| `--min-score N` | `90` | Score threshold for the high-scorers list (inclusive). |
| `--missing {report,drop,fill-mean}` | `report` | How to treat missing values (see below). |
| `--export-dir DIR` | off | Save high scorers and per-grade averages as CSV files in `DIR`. |
| `--plot-dir DIR` | `output` | Folder for the PNG charts. |
| `--show` | off | Also open chart windows. Needs a display. |
| `--no-plots` | off | Skip the charts. Cannot be combined with `--show`. |

Exit status is `0` on success, `1` for an expected failure such as a missing or
empty file (the message goes to stderr), and `2` for invalid arguments.

You can also run `python -m data_analyzer` instead of `analyzer`.

## What the report contains

Each section follows the tutorial, in the same order.

| Section | Tutorial step | Needs columns |
| --- | --- | --- |
| Dataset overview: shape, columns, first rows, types, `describe()` | Exploring the Data | any |
| Missing values per column | Handling Missing Data | any |
| Average, median, highest, lowest score | Calculating Basic Statistics | `score` |
| Students at or above `--min-score` | Filtering Data, Functions | `name`, `grade`, `score` |
| Students who studied more than 5 hours, and also attended more than 95% | Filtering Data | `name`, `study_hours`, `attendance` |
| Top scorer and most studious student (`idxmax`) | Finding Specific Students | `name`, `score`, `study_hours` |
| Average and summary per grade | Grouping Data | `grade`, `score` |
| Study hours and score correlation | Analyzing Study Time | `study_hours`, `score` |
| Scatter plot and bar chart (PNG) | Creating a Visualization | see plots |
| CSV export | Exporting Results | n/a |

The overview and missing-value sections work on **any** CSV. The other steps
need the student columns above. If a column is missing, the step is skipped
with a one-line notice instead of failing:

```text
== Study hours and scores ==
Skipped correlation: missing column(s) study_hours, score.
```

### The sample dataset

The bundled `students.csv` is the tutorial's fictional data (12 students,
grades 9 to 12, `score` on a 0 to 100 scale):

```csv
name,grade,study_hours,attendance,score
Ava,9,4.5,95,82
Liam,9,6.0,98,91
Sophia,10,3.5,89,76
Noah,10,7.0,99,94
Emma,11,5.5,93,88
Oliver,11,8.0,97,96
Mia,12,4.0,91,79
Ethan,12,6.5,96,90
Isabella,9,7.5,100,97
Lucas,10,2.5,85,68
Amelia,11,6.0,94,92
James,12,5.0,90,84
```

### Example output

This is an excerpt from a real run of `uv run analyzer`. The full report is in
[`sample-run.txt`](sample-run.txt).

```text
== Score statistics ==
Average: 86.42
Median: 89.00
Highest: 97
Lowest: 68

== Students with a score of 90 or higher ==
    name  grade  score
    Liam      9     91
    Noah     10     94
  Oliver     11     96
   Ethan     12     90
Isabella      9     97
  Amelia     11     92

== Standout students ==
Top scorer: Isabella (97)
Most study hours: Oliver (8 h)

== Scores by grade ==
Average score by grade:
grade
9     90.00
10    79.33
11    92.00
12    84.33

== Study hours and scores ==
Correlation: 0.98
(Correlation does not show that studying causes higher scores.)
```

The sample is small and fictional. Treat the patterns as illustrations, not as
evidence about real students.

## Missing data

Real files are rarely as clean as the sample. `--missing` chooses what happens
to the numeric columns the analysis uses (`grade`, `study_hours`, `attendance`,
`score`):

| Policy | Behavior |
| --- | --- |
| `report` (default) | Count missing values and change nothing. Statistics skip missing values. |
| `drop` | Remove rows that have a missing value in any of those columns, and say how many. |
| `fill-mean` | Fill missing `study_hours`, `attendance` and `score` with the column mean, and say how many. |

Text that is not a number (for example `abc` in `score`) is treated as a
missing value under every policy, and is counted separately so you can see it:

```text
== Missing values (policy: drop) ==
Missing values per column:
name           0
grade          0
study_hours    0
attendance     0
score          2
score: 1 non-numeric value(s) treated as missing.
Dropped 2 row(s) with missing values.
```

Two things to know about `fill-mean`:

- **`grade` is never filled.** A mean grade such as 10.5 is not a real grade.
  Rows with no grade are left out of the per-grade results.
- **Filling with the mean keeps the average but shrinks the spread.** The
  tutorial warns against replacing every missing value with an average. That is
  why the default only reports, and why filling is an explicit choice.

For a CSV with none of the student columns, the policy applies to every numeric
column instead.

## How this differs from the tutorial

| Tutorial | This project | Why |
| --- | --- | --- |
| `pip install pandas matplotlib` | `uv sync` with a locked `uv.lock` | Reproducible installs. |
| One script, `plt.show()` | Charts saved as PNG; `--show` opens windows | Works without a display (servers, CI). |
| Hard-coded column names and filename | Column-aware steps, `--file` | Reusable on other CSVs, as the tutorial suggests. |
| `fillna(mean)` shown as an option | `--missing`, default `report` | The tutorial warns against blind filling. |
| Bar chart plots unrounded means | Plots the two-decimal means shown in the report | The chart and the table agree. |
| `students.csv` created by hand | Bundled in the package | Works from any folder. |

## Project layout

```text
src/data_analyzer/
  cli.py        Argument parsing, exit codes, error messages
  analyzer.py   The workflow: runs each step in order and prints the report
  loader.py     Reading CSVs (and the bundled sample), with clear errors
  clean.py      Missing-data policies
  stats.py      Statistics, filters, groupings, correlation (pure functions)
  plots.py      Scatter plot and bar chart
  export.py     CSV export
  schema.py     Column names and thresholds
  errors.py     AnalyzerError for expected failures
  data/students.csv
tests/          pytest suite
```

`stats.py`, `clean.py` and `loader.py` can be imported on their own:

```python
from data_analyzer.loader import load_sample_dataset
from data_analyzer.stats import average_by_grade, high_scorers

data = load_sample_dataset()
print(high_scorers(data, minimum_score=95))
print(average_by_grade(data))
```

## Development

```bash
uv run pytest                  # tests, with a coverage gate of 90%
uv run ruff check .            # lint
uv run ruff format --check .   # formatting
```

The tests use the sample data and small hand-built tables. Expected values are
written out independently (for example with Python's `statistics` module)
rather than copied from the code's own output. No test opens a window.

## Known limitations

- **Thresholds are constants.** Study hours above 5 and attendance above 95%
  are in `schema.py`. Only the score threshold is a command-line option.
- **Column names are fixed.** There is no option to map your own column names
  onto `score`, `grade` and the rest.
- **Comma-separated, UTF-8 files only.** Other delimiters or encodings are
  reported as a parse error.
- **`grade` must be numeric.** Text such as `9th` is treated as missing.
- **No range checks.** A score of 250 or an attendance of -5 is analyzed as
  given.
- **Whole file in memory.** The CSV is read in one go, which is fine for
  spreadsheets and not for multi-gigabyte files.
- **Existing output is overwritten.** Charts and exports with the same file
  names replace earlier ones without asking.
- **Exports copy your data as-is.** If a cell starts with `=`, a spreadsheet may
  treat it as a formula when you open the exported CSV. Only open exports of
  files you trust.
- **`--show` needs a display.** On a server, use the saved PNGs.
