import pandas as pd
import pytest

from data_analyzer.clean import analysis_columns, clean


def test_report_policy_leaves_rows_and_values_alone(messy):
    result = clean(messy, "report")
    assert len(result.data) == 5
    assert result.dropped_rows == 0
    assert result.filled == {}
    assert result.data["study_hours"].isna().sum() == 1


def test_clean_never_modifies_the_input(messy):
    before = messy.copy()
    for policy in ("report", "drop", "fill-mean"):
        clean(messy, policy)
    pd.testing.assert_frame_equal(messy, before)


def test_null_counts_include_blank_and_non_numeric_cells(messy):
    result = clean(messy, "report")
    # score: one blank plus the text "abc"; grade: one blank; hours: one blank.
    assert result.null_counts["score"] == 2
    assert result.null_counts["grade"] == 1
    assert result.null_counts["study_hours"] == 1
    assert result.null_counts["name"] == 0


def test_non_numeric_text_is_converted_and_counted(messy):
    result = clean(messy, "report")
    assert result.coerced == {"score": 1}
    assert pd.api.types.is_numeric_dtype(result.data["score"])


def test_drop_removes_rows_missing_any_analysis_value(messy):
    result = clean(messy, "drop")
    # Rows B (blank score), C (blank grade), D (text score, blank hours) go.
    assert result.data["name"].tolist() == ["A", "E"]
    assert result.dropped_rows == 3


def test_fill_mean_fills_measures_with_the_column_mean(messy):
    result = clean(messy, "fill-mean")
    # Mean of the present scores 60, 80, 100 is 80; of hours 1, 2, 3, 5 is 2.75.
    assert result.data["score"].tolist() == [60, 80, 80, 80, 100]
    assert result.data["study_hours"].iloc[3] == pytest.approx(2.75)
    assert result.filled == {"study_hours": 1, "score": 2}
    assert len(result.data) == 5


def test_fill_mean_never_fills_grade(messy):
    result = clean(messy, "fill-mean")
    assert result.data["grade"].isna().sum() == 1
    assert "grade" not in result.filled


def test_grades_stay_whole_numbers_when_some_are_missing(messy):
    result = clean(messy, "report")
    assert str(result.data["grade"].dtype) == "Int64"
    assert result.data["grade"].dropna().tolist() == [9, 9, 10, 10]


def test_fill_mean_reports_columns_with_no_numbers(messy):
    messy["attendance"] = "n/a"
    result = clean(messy, "fill-mean")
    assert result.unfillable == ["attendance"]
    assert "attendance" not in result.filled


def test_unknown_policy_is_rejected(messy):
    with pytest.raises(ValueError, match="Unknown missing-data policy"):
        clean(messy, "median")  # type: ignore[arg-type]


def test_generic_csv_uses_its_numeric_columns():
    data = pd.DataFrame(
        {"city": ["a", "b", "c"], "sales": [1.0, None, 3.0], "ok": [True] * 3}
    )
    assert analysis_columns(data) == ["sales"]
    result = clean(data, "fill-mean")
    assert result.data["sales"].tolist() == [1.0, 2.0, 3.0]
    assert result.data["city"].tolist() == ["a", "b", "c"]
