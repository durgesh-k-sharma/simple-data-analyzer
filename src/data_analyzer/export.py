"""Writing analysis results to CSV files."""

from pathlib import Path

import pandas as pd

HIGH_SCORERS_FILE = "high_scoring_students.csv"
AVERAGE_BY_GRADE_FILE = "average_scores_by_grade.csv"


def export_results(
    export_dir: Path,
    *,
    high_scorers: pd.DataFrame | None = None,
    average_by_grade: pd.Series | None = None,
) -> list[Path]:
    """Save whichever results are provided as CSV files in ``export_dir``.

    Existing files with the same names are overwritten.

    Args:
        export_dir: Destination directory; created if it does not exist.
        high_scorers: Students at or above the score threshold.
        average_by_grade: Mean score per grade.

    Returns:
        The paths written, in a fixed order.

    Raises:
        OSError: If the directory or a file cannot be written.
    """
    written: list[Path] = []
    if high_scorers is None and average_by_grade is None:
        return written

    export_dir.mkdir(parents=True, exist_ok=True)
    if high_scorers is not None:
        path = export_dir / HIGH_SCORERS_FILE
        high_scorers.to_csv(path, index=False)
        written.append(path)
    if average_by_grade is not None:
        path = export_dir / AVERAGE_BY_GRADE_FILE
        average_by_grade.to_csv(path)
        written.append(path)
    return written
