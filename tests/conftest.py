"""Shared fixtures. Tests never open plot windows."""

import os

os.environ.setdefault("MPLBACKEND", "Agg")

import pandas as pd
import pytest

from data_analyzer.loader import load_sample_dataset

# Expected values are written out by hand (copied from the tutorial's table),
# so the tests do not just compare the code with itself.
NAMES = [
    "Ava", "Liam", "Sophia", "Noah", "Emma", "Oliver",
    "Mia", "Ethan", "Isabella", "Lucas", "Amelia", "James",
]  # fmt: skip
GRADES = [9, 9, 10, 10, 11, 11, 12, 12, 9, 10, 11, 12]
STUDY_HOURS = [4.5, 6.0, 3.5, 7.0, 5.5, 8.0, 4.0, 6.5, 7.5, 2.5, 6.0, 5.0]
ATTENDANCE = [95, 98, 89, 99, 93, 97, 91, 96, 100, 85, 94, 90]
SCORES = [82, 91, 76, 94, 88, 96, 79, 90, 97, 68, 92, 84]


@pytest.fixture
def sample() -> pd.DataFrame:
    """The bundled 12-row student dataset."""
    return load_sample_dataset()


@pytest.fixture
def messy() -> pd.DataFrame:
    """A small student table with a blank score, a text score and a blank grade."""
    return pd.DataFrame(
        {
            "name": ["A", "B", "C", "D", "E"],
            "grade": [9, 9, None, 10, 10],
            "study_hours": [1.0, 2.0, 3.0, None, 5.0],
            "attendance": [90, 91, 92, 93, 94],
            "score": [60, None, 80, "abc", 100],
        }
    )
