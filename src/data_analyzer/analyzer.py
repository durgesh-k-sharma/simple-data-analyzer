"""The analysis workflow: explore, check for missing data, analyze, plot, export.

This follows the order of the tutorial. Steps that depend on the student
columns are skipped, with a one-line notice, when a CSV does not have them.
"""

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TextIO

import pandas as pd

from data_analyzer import plots, stats
from data_analyzer.clean import CleanResult, MissingPolicy, clean
from data_analyzer.errors import AnalyzerError
from data_analyzer.export import export_results
from data_analyzer.schema import (
    ATTENDANCE,
    DEFAULT_MIN_SCORE,
    GRADE,
    HIGH_ATTENDANCE,
    HIGH_STUDY_HOURS,
    NAME,
    SCORE,
    STUDY_HOURS,
    absent_columns,
)


@dataclass(frozen=True)
class AnalysisConfig:
    """Options for one analysis run.

    Attributes:
        min_score: Score threshold for the "high scorers" list.
        missing: Missing-data policy: ``report``, ``drop`` or ``fill-mean``.
        plot_dir: Where to save PNG plots, or ``None`` for no plots.
        show: Also open plot windows (requires a display).
        export_dir: Where to save result CSVs, or ``None`` for no export.
    """

    min_score: float = DEFAULT_MIN_SCORE
    missing: MissingPolicy = "report"
    plot_dir: Path | None = Path("output")
    show: bool = False
    export_dir: Path | None = None


@dataclass
class AnalysisResult:
    """What a run produced, for callers that want more than the printed report."""

    cleaned: CleanResult
    high_scorers: pd.DataFrame | None = None
    average_by_grade: pd.Series | None = None
    plot_paths: list[Path] = field(default_factory=list)
    export_paths: list[Path] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


def run_analysis(
    data: pd.DataFrame,
    config: AnalysisConfig | None = None,
    out: TextIO | None = None,
) -> AnalysisResult:
    """Run the full analysis and print a report.

    Args:
        data: The loaded dataset. It is not modified.
        config: Run options; defaults to :class:`AnalysisConfig`.
        out: Where to print the report; defaults to ``sys.stdout``.

    Returns:
        An :class:`AnalysisResult` with the computed tables and written files.

    Raises:
        AnalyzerError: If plots or exports cannot be written.
    """
    config = config or AnalysisConfig()
    run = _Run(out or sys.stdout)

    _print_overview(run, data)
    cleaned = _handle_missing(run, data, config.missing)
    frame = cleaned.data
    result = AnalysisResult(cleaned=cleaned, skipped=run.skipped)

    _print_score_statistics(run, frame)
    result.high_scorers = _print_high_scorers(run, frame, config.min_score)
    _print_study_filters(run, frame)
    _print_extremes(run, frame)
    result.average_by_grade = _print_grade_analysis(run, frame)
    _print_correlation(run, frame)

    if config.plot_dir is not None:
        result.plot_paths = _make_plots(run, frame, config.plot_dir, config.show)
    if config.export_dir is not None:
        result.export_paths = _export(run, result, config.export_dir)
    return result


class _Run:
    """Output stream plus the list of skipped steps for one analysis run."""

    def __init__(self, out: TextIO) -> None:
        self.out = out
        self.skipped: list[str] = []

    def emit(self, text: str = "") -> None:
        print(text, file=self.out)

    def section(self, title: str) -> None:
        self.emit(f"\n== {title} ==")

    def table(self, frame: pd.DataFrame | pd.Series) -> None:
        self.emit(frame.to_string())

    def needs(self, frame: pd.DataFrame, step: str, columns: list[str]) -> bool:
        """Return True if all columns exist; otherwise print a notice and skip."""
        absent = absent_columns(frame, columns)
        if absent:
            self.emit(f"Skipped {step}: missing column(s) {', '.join(absent)}.")
            self.skipped.append(step)
            return False
        return True


def _print_overview(run: _Run, data: pd.DataFrame) -> None:
    run.section("Dataset overview")
    run.emit(f"Shape: {data.shape}")
    run.emit(f"Columns: {', '.join(map(str, data.columns))}")
    run.emit("\nFirst five rows:")
    run.table(data.head())
    run.emit("\nColumn types:")
    data.info(buf=run.out)
    run.emit("Numeric summary:")
    run.table(data.describe())


def _handle_missing(
    run: _Run, data: pd.DataFrame, policy: MissingPolicy
) -> CleanResult:
    cleaned = clean(data, policy)

    run.section(f"Missing values (policy: {policy})")
    run.emit("Missing values per column:")
    run.table(cleaned.null_counts)
    for column, count in cleaned.coerced.items():
        run.emit(f"{column}: {count} non-numeric value(s) treated as missing.")
    if policy == "report":
        run.emit("Data left unchanged; statistics skip missing values.")
    elif policy == "drop":
        run.emit(f"Dropped {cleaned.dropped_rows} row(s) with missing values.")
    else:
        for column, count in cleaned.filled.items():
            run.emit(f"Filled {count} missing value(s) in {column} with its mean.")
        for column in cleaned.unfillable:
            run.emit(f"Could not fill {column}: it has no numeric values.")
        if not cleaned.filled and not cleaned.unfillable:
            run.emit("Nothing to fill.")
    return cleaned


def _print_score_statistics(run: _Run, frame: pd.DataFrame) -> None:
    run.section("Score statistics")
    if not run.needs(frame, "score statistics", [SCORE]):
        return
    summary = stats.score_statistics(frame)
    if summary is None:
        run.emit("No score values available.")
        return
    run.emit(f"Average: {summary.average:.2f}")
    run.emit(f"Median: {summary.median:.2f}")
    run.emit(f"Highest: {summary.highest:g}")
    run.emit(f"Lowest: {summary.lowest:g}")


def _print_high_scorers(
    run: _Run, frame: pd.DataFrame, minimum_score: float
) -> pd.DataFrame | None:
    run.section(f"Students with a score of {minimum_score:g} or higher")
    if not run.needs(frame, "high scorers", [NAME, GRADE, SCORE]):
        return None
    scorers = stats.high_scorers(frame, minimum_score)
    run.emit(scorers.to_string(index=False) if not scorers.empty else "(none)")
    return scorers


def _print_study_filters(run: _Run, frame: pd.DataFrame) -> None:
    run.section("Study habits")
    if not run.needs(frame, "study-habit filters", [NAME, STUDY_HOURS, ATTENDANCE]):
        return
    columns = [NAME, STUDY_HOURS, ATTENDANCE]
    studiers = stats.frequent_studiers(frame)[columns]
    run.emit(f"Studied more than {HIGH_STUDY_HOURS:g} hours:")
    run.emit(studiers.to_string(index=False) if not studiers.empty else "(none)")
    committed = stats.committed_students(frame)[columns]
    run.emit(
        f"\nStudied more than {HIGH_STUDY_HOURS:g} hours "
        f"and attendance above {HIGH_ATTENDANCE:g}%:"
    )
    run.emit(committed.to_string(index=False) if not committed.empty else "(none)")


def _print_extremes(run: _Run, frame: pd.DataFrame) -> None:
    run.section("Standout students")
    if not run.needs(frame, "standout students", [NAME, SCORE, STUDY_HOURS]):
        return
    best = stats.top_scorer(frame)
    if best is None:
        run.emit("Top scorer: no scores available.")
    else:
        run.emit(f"Top scorer: {best[NAME]} ({best[SCORE]:g})")
    hardest = stats.most_studious(frame)
    if hardest is None:
        run.emit("Most study hours: no study hours available.")
    else:
        run.emit(f"Most study hours: {hardest[NAME]} ({hardest[STUDY_HOURS]:g} h)")


def _print_grade_analysis(run: _Run, frame: pd.DataFrame) -> pd.Series | None:
    run.section("Scores by grade")
    if not run.needs(frame, "grade analysis", [GRADE, SCORE]):
        return None
    averages = stats.average_by_grade(frame)
    run.emit("Average score by grade:")
    run.table(averages)
    run.emit("\nSummary by grade:")
    run.table(stats.grade_summary(frame))
    return averages


def _print_correlation(run: _Run, frame: pd.DataFrame) -> None:
    run.section("Study hours and scores")
    if not run.needs(frame, "correlation", [STUDY_HOURS, SCORE]):
        return
    value = stats.study_score_correlation(frame)
    if value is None:
        run.emit("Correlation: not enough data to calculate.")
        return
    run.emit(f"Correlation: {value:.2f}")
    run.emit("(Correlation does not show that studying causes higher scores.)")


def _make_plots(
    run: _Run, frame: pd.DataFrame, plot_dir: Path, show: bool
) -> list[Path]:
    run.section("Plots")
    kinds: list[plots.PlotKind] = []
    if run.needs(frame, "scatter plot", [STUDY_HOURS, SCORE]):
        if plots.has_scatter_data(frame):
            kinds.append("scatter")
        else:
            run.emit("Skipped scatter plot: no rows with both values.")
            run.skipped.append("scatter plot")
    if run.needs(frame, "bar chart", [GRADE, SCORE]):
        if plots.has_bar_data(frame):
            kinds.append("bar")
        else:
            run.emit("Skipped bar chart: no rows with both values.")
            run.skipped.append("bar chart")
    if not kinds:
        return []
    try:
        paths = plots.render_plots(frame, kinds, plot_dir, show=show)
    except OSError as exc:
        raise AnalyzerError(
            f"Could not write plots to {plot_dir}: {exc.strerror or exc}"
        ) from exc
    for path in paths:
        run.emit(f"Saved plot: {path}")
    return paths


def _export(run: _Run, result: AnalysisResult, export_dir: Path) -> list[Path]:
    run.section("Export")
    try:
        paths = export_results(
            export_dir,
            high_scorers=result.high_scorers,
            average_by_grade=result.average_by_grade,
        )
    except OSError as exc:
        raise AnalyzerError(
            f"Could not write results to {export_dir}: {exc.strerror or exc}"
        ) from exc
    if not paths:
        run.emit("Nothing to export: no student results were computed.")
    for path in paths:
        run.emit(f"Saved results: {path}")
    return paths
