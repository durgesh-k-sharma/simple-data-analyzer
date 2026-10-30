"""Column names and thresholds for the student-performance dataset.

The tutorial hard-codes these names throughout its analysis code. Collecting
them here lets each analysis step declare which columns it needs, so the
analyzer can skip a step with a clear notice when a CSV does not have them.
"""

from collections.abc import Iterable

import pandas as pd

NAME = "name"
GRADE = "grade"
STUDY_HOURS = "study_hours"
ATTENDANCE = "attendance"
SCORE = "score"

#: Columns that hold numbers. Non-numeric text in these is treated as missing.
NUMERIC_COLUMNS = (GRADE, STUDY_HOURS, ATTENDANCE, SCORE)

#: Default for ``--min-score``: the tutorial's "high score" cut-off.
DEFAULT_MIN_SCORE = 90.0
#: The tutorial's "studies a lot" threshold (hours, exclusive).
HIGH_STUDY_HOURS = 5.0
#: The tutorial's "attends reliably" threshold (percent, exclusive).
HIGH_ATTENDANCE = 95.0


def absent_columns(data: pd.DataFrame, required: Iterable[str]) -> list[str]:
    """Return the names in ``required`` that ``data`` does not have, in order."""
    return [column for column in required if column not in data.columns]
