import io

import pandas as pd
import pytest

from data_analyzer.analyzer import AnalysisConfig, run_analysis
from data_analyzer.errors import AnalyzerError


def run(data, tmp_path, **overrides):
    """Run the analysis quietly into a buffer; return (result, printed text)."""
    options = {"plot_dir": tmp_path / "plots"} | overrides
    buffer = io.StringIO()
    result = run_analysis(data, AnalysisConfig(**options), buffer)
    return result, buffer.getvalue()


def test_report_for_the_sample_contains_the_tutorial_numbers(sample, tmp_path):
    _, text = run(sample, tmp_path)
    for expected in [
        "Shape: (12, 5)",
        "Average: 86.42",
        "Median: 89.00",
        "Highest: 97",
        "Lowest: 68",
        "Top scorer: Isabella (97)",
        "Most study hours: Oliver (8 h)",
        "Correlation: 0.98",
        "Students with a score of 90 or higher",
    ]:
        assert expected in text


def test_sample_run_produces_tables_and_plots(sample, tmp_path):
    result, _ = run(sample, tmp_path)
    assert len(result.high_scorers) == 6
    assert result.average_by_grade.to_dict() == {
        9: 90.0,
        10: 79.33,
        11: 92.0,
        12: 84.33,
    }
    assert [p.suffix for p in result.plot_paths] == [".png", ".png"]
    assert result.skipped == []


def test_min_score_changes_the_filter(sample, tmp_path):
    result, text = run(sample, tmp_path, min_score=95)
    assert result.high_scorers["name"].tolist() == ["Oliver", "Isabella"]
    assert "score of 95 or higher" in text


def test_input_dataframe_is_not_modified(messy, tmp_path):
    before = messy.copy()
    run(messy, tmp_path, missing="fill-mean")
    pd.testing.assert_frame_equal(messy, before)


def test_generic_csv_gets_overview_but_skips_student_steps(tmp_path):
    data = pd.DataFrame({"city": ["a", "b", "c"], "sales": [10, 20, 30]})
    result, text = run(data, tmp_path)
    assert "Shape: (3, 2)" in text
    assert "Missing values per column" in text
    assert "Skipped score statistics: missing column(s) score." in text
    assert "Skipped correlation: missing column(s) study_hours, score." in text
    assert result.plot_paths == []
    assert result.high_scorers is None and result.average_by_grade is None
    assert not (tmp_path / "plots").exists()
    assert "scatter plot" in result.skipped and "bar chart" in result.skipped


def test_partial_student_csv_runs_only_the_steps_it_can(tmp_path):
    data = pd.DataFrame({"score": [50, 70, 90]})
    result, text = run(data, tmp_path)
    assert "Average: 70.00" in text
    assert "Skipped high scorers: missing column(s) name, grade." in text
    assert "grade analysis" in result.skipped


def test_report_policy_counts_missing_values_without_changing_data(messy, tmp_path):
    result, text = run(messy, tmp_path)
    assert "policy: report" in text
    assert "Data left unchanged" in text
    assert "score: 1 non-numeric value(s) treated as missing." in text
    assert len(result.cleaned.data) == 5


def test_drop_policy_reports_removed_rows(messy, tmp_path):
    result, text = run(messy, tmp_path, missing="drop")
    assert "Dropped 3 row(s) with missing values." in text
    assert len(result.cleaned.data) == 2


def test_fill_mean_policy_reports_what_was_filled(messy, tmp_path):
    _, text = run(messy, tmp_path, missing="fill-mean")
    assert "Filled 2 missing value(s) in score with its mean." in text
    assert "Filled 1 missing value(s) in study_hours with its mean." in text


def test_fill_mean_with_nothing_missing_says_so(sample, tmp_path):
    _, text = run(sample, tmp_path, missing="fill-mean")
    assert "Nothing to fill." in text


def test_fill_mean_names_columns_it_cannot_fill(sample, tmp_path):
    sample["attendance"] = "n/a"
    _, text = run(sample, tmp_path, missing="fill-mean")
    assert "Could not fill attendance: it has no numeric values." in text


def test_dropping_every_row_degrades_gracefully(tmp_path):
    data = pd.DataFrame(
        {
            "name": ["a", "b"],
            "grade": [9, 10],
            "study_hours": [1.0, 2.0],
            "attendance": [90, 91],
            "score": ["x", "y"],
        }
    )
    result, text = run(data, tmp_path, missing="drop")
    assert "Dropped 2 row(s)" in text
    assert "No score values available." in text
    assert "Top scorer: no scores available." in text
    assert "Correlation: not enough data to calculate." in text
    assert "Skipped scatter plot: no rows with both values." in text
    assert result.plot_paths == []


def test_no_plot_dir_means_no_plots(sample, tmp_path):
    result, text = run(sample, tmp_path, plot_dir=None)
    assert result.plot_paths == []
    assert "== Plots ==" not in text


def test_export_writes_files_and_lists_them(sample, tmp_path):
    result, text = run(sample, tmp_path, export_dir=tmp_path / "exp")
    assert [p.name for p in result.export_paths] == [
        "high_scoring_students.csv",
        "average_scores_by_grade.csv",
    ]
    assert "Saved results:" in text


def test_export_with_nothing_computed_says_so(tmp_path):
    data = pd.DataFrame({"x": [1, 2]})
    result, text = run(data, tmp_path, export_dir=tmp_path / "exp")
    assert result.export_paths == []
    assert "Nothing to export" in text
    assert not (tmp_path / "exp").exists()


def test_unwritable_plot_dir_becomes_analyzer_error(sample, tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("x")
    with pytest.raises(AnalyzerError, match="Could not write plots"):
        run(sample, tmp_path, plot_dir=blocker / "sub")


def test_unwritable_export_dir_becomes_analyzer_error(sample, tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("x")
    with pytest.raises(AnalyzerError, match="Could not write results"):
        run(sample, tmp_path, export_dir=blocker / "sub")


def test_default_config_prints_to_stdout(sample, tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    run_analysis(sample)
    assert "Shape: (12, 5)" in capsys.readouterr().out
    assert (tmp_path / "output" / "study_hours_vs_score.png").exists()
