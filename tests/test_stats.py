import statistics
import warnings

import numpy as np
import pandas as pd
import pytest

from conftest import SCORES, STUDY_HOURS
from data_analyzer import stats


def names(frame: pd.DataFrame) -> list[str]:
    return frame["name"].tolist()


def test_score_statistics_match_independent_calculation(sample):
    result = stats.score_statistics(sample)
    assert result is not None
    assert result.average == pytest.approx(statistics.mean(SCORES))
    assert result.average == pytest.approx(1037 / 12)
    assert result.median == 89
    assert result.highest == 97
    assert result.lowest == 68


def test_score_statistics_ignore_missing_values(sample):
    sample.loc[0, "score"] = np.nan
    result = stats.score_statistics(sample)
    assert result is not None
    assert result.average == pytest.approx(statistics.mean(SCORES[1:]))


def test_score_statistics_is_none_without_scores(sample):
    sample["score"] = np.nan
    assert stats.score_statistics(sample) is None


def test_high_scorers_default_threshold_includes_the_boundary(sample):
    result = stats.high_scorers(sample, 90)
    assert names(result) == ["Liam", "Noah", "Oliver", "Ethan", "Isabella", "Amelia"]
    assert list(result.columns) == ["name", "grade", "score"]


def test_high_scorers_with_a_higher_threshold(sample):
    assert names(stats.high_scorers(sample, 95)) == ["Oliver", "Isabella"]


def test_high_scorers_can_be_empty(sample):
    assert stats.high_scorers(sample, 100).empty


def test_high_scorers_excludes_missing_scores(sample):
    sample.loc[sample["name"] == "Isabella", "score"] = np.nan
    assert "Isabella" not in names(stats.high_scorers(sample, 90))


def test_frequent_studiers_excludes_exactly_five_hours(sample):
    result = stats.frequent_studiers(sample)
    assert names(result) == [
        "Liam", "Noah", "Emma", "Oliver", "Ethan", "Isabella", "Amelia",
    ]  # fmt: skip
    assert "James" not in names(result)  # studied exactly 5.0 hours


def test_committed_students_need_both_conditions(sample):
    result = stats.committed_students(sample)
    assert names(result) == ["Liam", "Noah", "Oliver", "Ethan", "Isabella"]
    assert "Amelia" not in names(result)  # 6 hours but only 94% attendance


def test_top_scorer_and_most_studious(sample):
    top = stats.top_scorer(sample)
    hardest = stats.most_studious(sample)
    assert top is not None and hardest is not None
    assert (top["name"], top["score"]) == ("Isabella", 97)
    assert (hardest["name"], hardest["study_hours"]) == ("Oliver", 8.0)


def test_top_scorer_picks_the_first_on_ties():
    data = pd.DataFrame({"name": ["a", "b"], "score": [90, 90]})
    top = stats.top_scorer(data)
    assert top is not None and top["name"] == "a"


def test_top_scorer_is_none_when_all_scores_missing(sample):
    sample["score"] = np.nan
    assert stats.top_scorer(sample) is None


def test_average_by_grade_is_rounded_to_two_decimals(sample):
    result = stats.average_by_grade(sample)
    assert result.to_dict() == {9: 90.0, 10: 79.33, 11: 92.0, 12: 84.33}


def test_grade_summary_has_four_columns_and_three_students_per_grade(sample):
    result = stats.grade_summary(sample)
    assert list(result.columns) == ["mean", "min", "max", "count"]
    assert result["count"].tolist() == [3, 3, 3, 3]
    assert result.loc[10, "min"] == 68
    assert result.loc[10, "max"] == 94


def test_correlation_matches_the_standard_library(sample):
    expected = statistics.correlation(STUDY_HOURS, SCORES)
    value = stats.study_score_correlation(sample)
    assert value == pytest.approx(expected)
    assert round(value, 2) == 0.98


def test_correlation_is_none_when_undefined():
    one_row = pd.DataFrame({"study_hours": [3.0], "score": [80]})
    constant = pd.DataFrame({"study_hours": [3.0, 3.0, 3.0], "score": [1, 2, 3]})
    assert stats.study_score_correlation(one_row) is None
    assert stats.study_score_correlation(constant) is None


def test_row_lookups_return_one_row_even_with_repeated_index_labels():
    data = pd.concat(
        [
            pd.DataFrame({"name": ["a"], "score": [50], "study_hours": [9.0]}),
            pd.DataFrame({"name": ["b"], "score": [99], "study_hours": [1.0]}),
        ]
    )  # both rows are labelled 0
    top = stats.top_scorer(data)
    hardest = stats.most_studious(data)
    assert isinstance(top, pd.Series) and top["name"] == "b"
    assert isinstance(hardest, pd.Series) and hardest["name"] == "a"


def test_undefined_correlation_emits_no_warnings():
    constant = pd.DataFrame({"study_hours": [3.0, 3.0, 3.0], "score": [1, 2, 3]})
    one_row = pd.DataFrame({"study_hours": [3.0], "score": [80]})
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert stats.study_score_correlation(constant) is None
        assert stats.study_score_correlation(one_row) is None


def test_correlation_ignores_rows_with_a_missing_value(sample):
    sample.loc[0, "study_hours"] = np.nan
    expected = statistics.correlation(STUDY_HOURS[1:], SCORES[1:])
    assert stats.study_score_correlation(sample) == pytest.approx(expected)
