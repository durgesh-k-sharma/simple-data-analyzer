import pytest

from conftest import ATTENDANCE, GRADES, NAMES, SCORES, STUDY_HOURS
from data_analyzer.errors import AnalyzerError
from data_analyzer.loader import load_csv, load_sample_dataset


def test_sample_dataset_matches_tutorial_table():
    data = load_sample_dataset()
    assert data.shape == (12, 5)
    assert list(data.columns) == [
        "name", "grade", "study_hours", "attendance", "score",
    ]  # fmt: skip
    assert data["name"].tolist() == NAMES
    assert data["grade"].tolist() == GRADES
    assert data["study_hours"].tolist() == STUDY_HOURS
    assert data["attendance"].tolist() == ATTENDANCE
    assert data["score"].tolist() == SCORES


def test_load_csv_reads_a_file(tmp_path):
    path = tmp_path / "x.csv"
    path.write_text("a,b\n1,2\n3,4\n")
    assert load_csv(path).shape == (2, 2)


def test_missing_file_raises_analyzer_error(tmp_path):
    with pytest.raises(AnalyzerError, match="File not found"):
        load_csv(tmp_path / "nope.csv")


def test_zero_byte_file_raises_analyzer_error(tmp_path):
    path = tmp_path / "empty.csv"
    path.write_text("")
    with pytest.raises(AnalyzerError, match="empty"):
        load_csv(path)


def test_header_only_file_raises_analyzer_error(tmp_path):
    path = tmp_path / "header.csv"
    path.write_text("name,score\n")
    with pytest.raises(AnalyzerError, match="no data rows"):
        load_csv(path)


def test_directory_raises_analyzer_error(tmp_path):
    with pytest.raises(AnalyzerError, match="Cannot read"):
        load_csv(tmp_path)


def test_ragged_rows_raise_analyzer_error(tmp_path):
    path = tmp_path / "ragged.csv"
    path.write_text("a,b\n1,2\n1,2,3,4\n")
    with pytest.raises(AnalyzerError, match="Could not parse"):
        load_csv(path)


def test_undecodable_bytes_raise_analyzer_error(tmp_path):
    path = tmp_path / "binary.csv"
    path.write_bytes(b"name,score\n\xff\xfe\x80,1\n")
    with pytest.raises(AnalyzerError, match="Could not parse"):
        load_csv(path)
