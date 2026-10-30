"""Statistics, filters and groupings from the tutorial, as reusable functions.

Every function expects the columns it names to exist; the caller checks with
:func:`data_analyzer.schema.absent_columns` first. Functions that can have no
answer (for example every score is missing) return ``None`` instead of raising.
"""

from dataclasses import dataclass

import pandas as pd

from data_analyzer.schema import (
    ATTENDANCE,
    GRADE,
    HIGH_ATTENDANCE,
    HIGH_STUDY_HOURS,
    NAME,
    SCORE,
    STUDY_HOURS,
)


@dataclass(frozen=True)
class ScoreStats:
    """Summary statistics for the ``score`` column."""

    average: float
    median: float
    highest: float
    lowest: float


def score_statistics(data: pd.DataFrame) -> ScoreStats | None:
    """Return mean, median, max and min of ``score``, ignoring missing values.

    Returns:
        The statistics, or ``None`` if there are no scores.
    """
    scores = data[SCORE].dropna()
    if scores.empty:
        return None
    return ScoreStats(
        average=float(scores.mean()),
        median=float(scores.median()),
        highest=float(scores.max()),
        lowest=float(scores.min()),
    )


def high_scorers(data: pd.DataFrame, minimum_score: float) -> pd.DataFrame:
    """Return name, grade and score for students scoring at least ``minimum_score``."""
    return data.loc[data[SCORE] >= minimum_score, [NAME, GRADE, SCORE]]


def frequent_studiers(
    data: pd.DataFrame, minimum_hours: float = HIGH_STUDY_HOURS
) -> pd.DataFrame:
    """Return students who studied more than ``minimum_hours``."""
    return data.loc[data[STUDY_HOURS] > minimum_hours]


def committed_students(
    data: pd.DataFrame,
    minimum_hours: float = HIGH_STUDY_HOURS,
    minimum_attendance: float = HIGH_ATTENDANCE,
) -> pd.DataFrame:
    """Return students who studied more than ``minimum_hours`` *and* attended
    more than ``minimum_attendance`` percent of the time."""
    mask = (data[STUDY_HOURS] > minimum_hours) & (data[ATTENDANCE] > minimum_attendance)
    return data.loc[mask]


def top_scorer(data: pd.DataFrame) -> pd.Series | None:
    """Return the row with the highest score (first one on ties), or ``None``."""
    return _row_with_max(data, SCORE)


def most_studious(data: pd.DataFrame) -> pd.Series | None:
    """Return the row with the most study hours (first one on ties), or ``None``."""
    return _row_with_max(data, STUDY_HOURS)


def _row_with_max(data: pd.DataFrame, column: str) -> pd.Series | None:
    if data[column].dropna().empty:
        return None
    # Look the row up by position, not label: labels can repeat (for example
    # after pd.concat), and a repeated label would return several rows.
    return data.iloc[data[column].argmax()]


def average_by_grade(data: pd.DataFrame) -> pd.Series:
    """Return the mean score per grade, rounded to two decimals.

    Rows with a missing grade or score are left out of the groups.
    """
    return data.groupby(GRADE)[SCORE].mean().round(2)


def grade_summary(data: pd.DataFrame) -> pd.DataFrame:
    """Return mean, min, max and count of score for each grade."""
    return data.groupby(GRADE)[SCORE].agg(["mean", "min", "max", "count"])


def study_score_correlation(data: pd.DataFrame) -> float | None:
    """Return the Pearson correlation of study hours and score.

    Returns:
        A value from -1 to 1, or ``None`` if it is undefined (fewer than two
        complete pairs, or one column never changes).

    Note:
        Correlation does not show that studying causes higher scores.
    """
    pairs = data[[STUDY_HOURS, SCORE]].dropna()
    # Check the degenerate cases up front: letting numpy divide by a zero
    # standard deviation works, but prints RuntimeWarnings on some versions.
    if len(pairs) < 2 or (pairs.nunique() < 2).any():
        return None
    return float(pairs[STUDY_HOURS].corr(pairs[SCORE]))
