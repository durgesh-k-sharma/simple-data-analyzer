import pandas as pd

from data_analyzer import stats
from data_analyzer.export import export_results


def test_exports_both_results(sample, tmp_path):
    paths = export_results(
        tmp_path,
        high_scorers=stats.high_scorers(sample, 90),
        average_by_grade=stats.average_by_grade(sample),
    )
    assert [p.name for p in paths] == [
        "high_scoring_students.csv",
        "average_scores_by_grade.csv",
    ]


def test_high_scorers_csv_has_no_index_column(sample, tmp_path):
    export_results(tmp_path, high_scorers=stats.high_scorers(sample, 90))
    saved = pd.read_csv(tmp_path / "high_scoring_students.csv")
    assert list(saved.columns) == ["name", "grade", "score"]
    assert len(saved) == 6


def test_average_by_grade_csv_round_trips(sample, tmp_path):
    export_results(tmp_path, average_by_grade=stats.average_by_grade(sample))
    saved = pd.read_csv(tmp_path / "average_scores_by_grade.csv", index_col="grade")
    assert saved["score"].to_dict() == {9: 90.0, 10: 79.33, 11: 92.0, 12: 84.33}


def test_only_provided_results_are_written(sample, tmp_path):
    paths = export_results(tmp_path, average_by_grade=stats.average_by_grade(sample))
    assert [p.name for p in paths] == ["average_scores_by_grade.csv"]
    assert not (tmp_path / "high_scoring_students.csv").exists()


def test_nothing_provided_writes_nothing_and_creates_no_directory(tmp_path):
    target = tmp_path / "out"
    assert export_results(target) == []
    assert not target.exists()


def test_creates_directories_and_overwrites_existing_files(sample, tmp_path):
    target = tmp_path / "deep" / "er"
    first = stats.high_scorers(sample, 90)
    export_results(target, high_scorers=first)
    export_results(target, high_scorers=stats.high_scorers(sample, 95))
    assert len(pd.read_csv(target / "high_scoring_students.csv")) == 2
