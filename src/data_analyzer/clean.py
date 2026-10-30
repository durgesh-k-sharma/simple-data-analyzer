"""Missing-data handling.

Real files are rarely as tidy as the tutorial's sample. This module applies one
of three policies to the columns that the analysis depends on:

``report``    Leave the data alone; only count what is missing (the default).
``drop``      Drop rows that have a missing value in any analysis column.
``fill-mean`` Fill missing measurements with that column's mean.

Text that cannot be read as a number (``"abc"`` in ``score``) is converted to
NaN first, so it is counted and handled exactly like a blank cell.
"""

from dataclasses import dataclass, field
from typing import Literal

import pandas as pd
from pandas.api.types import is_bool_dtype, is_numeric_dtype

from data_analyzer.schema import GRADE, NUMERIC_COLUMNS

MissingPolicy = Literal["report", "drop", "fill-mean"]
MISSING_POLICIES: tuple[MissingPolicy, ...] = ("report", "drop", "fill-mean")


@dataclass
class CleanResult:
    """The outcome of applying a missing-data policy.

    Attributes:
        data: The DataFrame to analyze (a copy; the input is never modified).
        null_counts: Missing values per column, after text-to-NaN conversion
            and before the policy was applied.
        coerced: Columns where non-numeric text was converted to NaN, with the
            number of values converted.
        dropped_rows: Rows removed by the ``drop`` policy.
        filled: Values filled per column by the ``fill-mean`` policy.
        unfillable: Columns the ``fill-mean`` policy could not fill because
            they contain no numbers at all.
    """

    data: pd.DataFrame
    null_counts: pd.Series
    coerced: dict[str, int] = field(default_factory=dict)
    dropped_rows: int = 0
    filled: dict[str, int] = field(default_factory=dict)
    unfillable: list[str] = field(default_factory=list)


def analysis_columns(data: pd.DataFrame) -> list[str]:
    """Return the columns the missing-data policy applies to.

    These are the known student columns that are present. For a CSV with none
    of them, it falls back to every numeric column.
    """
    known = [column for column in NUMERIC_COLUMNS if column in data.columns]
    if known:
        return known
    return [
        column
        for column in data.columns
        if is_numeric_dtype(data[column]) and not is_bool_dtype(data[column])
    ]


def clean(data: pd.DataFrame, policy: MissingPolicy = "report") -> CleanResult:
    """Apply a missing-data policy to a copy of ``data``.

    Args:
        data: The loaded DataFrame. It is not modified.
        policy: One of ``"report"``, ``"drop"`` or ``"fill-mean"``.

    Returns:
        A :class:`CleanResult` with the data to analyze and a record of what
        was counted, converted, dropped or filled.

    Raises:
        ValueError: If ``policy`` is not a known policy.
    """
    if policy not in MISSING_POLICIES:
        raise ValueError(f"Unknown missing-data policy: {policy!r}")

    work = data.copy()
    columns = analysis_columns(work)
    coerced = _coerce_to_numeric(work, columns)
    null_counts = work.isna().sum()

    result = CleanResult(data=work, null_counts=null_counts, coerced=coerced)
    if policy == "drop":
        before = len(work)
        result.data = work.dropna(subset=columns)
        result.dropped_rows = before - len(result.data)
    elif policy == "fill-mean":
        # A mean grade (e.g. 10.5) is meaningless, so grades are never filled.
        _fill_with_mean(result, [column for column in columns if column != GRADE])
    return result


def _coerce_to_numeric(work: pd.DataFrame, columns: list[str]) -> dict[str, int]:
    """Convert text in numeric columns to NaN in place; return counts per column."""
    coerced: dict[str, int] = {}
    for column in columns:
        if is_numeric_dtype(work[column]):
            continue
        before = int(work[column].isna().sum())
        work[column] = pd.to_numeric(work[column], errors="coerce")
        converted = int(work[column].isna().sum()) - before
        if converted:
            coerced[column] = converted

    if GRADE in columns:
        grades = work[GRADE]
        if (grades.dropna() % 1 == 0).all():
            # Keep grades as whole numbers (9, not 9.0) even when some are missing.
            work[GRADE] = grades.astype("Int64")
    return coerced


def _fill_with_mean(result: CleanResult, columns: list[str]) -> None:
    for column in columns:
        values = result.data[column]
        missing = int(values.isna().sum())
        if not missing:
            continue
        if missing == len(values):
            result.unfillable.append(column)
            continue
        result.data[column] = values.fillna(values.mean())
        result.filled[column] = missing
