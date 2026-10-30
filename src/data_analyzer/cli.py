"""Command-line interface: ``uv run analyzer [options]``."""

import argparse
import contextlib
import math
import os
import sys
from collections.abc import Sequence
from pathlib import Path

from data_analyzer.analyzer import AnalysisConfig, run_analysis
from data_analyzer.clean import MISSING_POLICIES
from data_analyzer.errors import AnalyzerError
from data_analyzer.loader import SAMPLE_DATASET_NAME, load_csv, load_sample_dataset
from data_analyzer.schema import DEFAULT_MIN_SCORE

DEFAULT_PLOT_DIR = Path("output")


def _finite_float(text: str) -> float:
    try:
        value = float(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not a number: {text!r}") from None
    if not math.isfinite(value):
        raise argparse.ArgumentTypeError(f"must be a finite number, got {text!r}")
    return value


def build_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the ``analyzer`` command."""
    parser = argparse.ArgumentParser(
        prog="analyzer",
        description=(
            "Analyze a CSV file with pandas. With no --file, analyzes the bundled "
            f"{SAMPLE_DATASET_NAME} student-performance sample."
        ),
    )
    parser.add_argument(
        "--file", type=Path, help="CSV file to analyze (default: bundled sample)"
    )
    parser.add_argument(
        "--min-score",
        type=_finite_float,
        default=DEFAULT_MIN_SCORE,
        help="score threshold for the high-scorers list (default: %(default)g)",
    )
    parser.add_argument(
        "--missing",
        choices=MISSING_POLICIES,
        default="report",
        help=(
            "how to treat missing values: report them only, drop affected rows, "
            "or fill measurements with the column mean (default: %(default)s)"
        ),
    )
    parser.add_argument(
        "--export-dir",
        type=Path,
        help="save high scorers and per-grade averages as CSV files in this folder",
    )
    parser.add_argument(
        "--plot-dir",
        type=Path,
        default=DEFAULT_PLOT_DIR,
        help="folder for PNG plots (default: %(default)s)",
    )
    plot_mode = parser.add_mutually_exclusive_group()
    plot_mode.add_argument(
        "--show", action="store_true", help="also open plot windows (needs a display)"
    )
    plot_mode.add_argument(
        "--no-plots", action="store_true", help="do not create any plots"
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the analyzer.

    Args:
        argv: Command-line arguments, excluding the program name. Defaults to
            ``sys.argv[1:]``.

    Returns:
        0 on success, 1 on an expected failure such as a missing file. Invalid
        arguments make argparse exit with status 2.
    """
    args = build_parser().parse_args(argv)
    config = AnalysisConfig(
        min_score=args.min_score,
        missing=args.missing,
        plot_dir=None if args.no_plots else args.plot_dir,
        show=args.show,
        export_dir=args.export_dir,
    )
    try:
        if args.file is None:
            print(
                "No --file given; analyzing the bundled sample "
                f"({SAMPLE_DATASET_NAME})."
            )
            data = load_sample_dataset()
        else:
            data = load_csv(args.file)
        run_analysis(data, config)
        sys.stdout.flush()  # surface a closed pipe here, not at interpreter exit
    except AnalyzerError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except BrokenPipeError:
        # The reader went away (for example `analyzer | head`). Not a bug, so no
        # traceback; point stdout at /dev/null so the exit-time flush stays quiet.
        _silence_stdout()
        return 1
    return 0


def _silence_stdout() -> None:
    # Suppress errors for a stdout with no file descriptor to redirect.
    with contextlib.suppress(OSError, ValueError):
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
