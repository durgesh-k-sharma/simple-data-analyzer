import subprocess
import sys

import pandas as pd
import pytest

from data_analyzer.cli import main


@pytest.fixture(autouse=True)
def in_tmp_cwd(tmp_path, monkeypatch):
    """Run every CLI test in an empty folder so default output/ stays contained."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_default_run_uses_the_bundled_sample(in_tmp_cwd, capsys):
    assert main([]) == 0
    out = capsys.readouterr().out
    assert "analyzing the bundled sample (students.csv)" in out
    assert "Average: 86.42" in out
    assert (in_tmp_cwd / "output" / "study_hours_vs_score.png").exists()
    assert (in_tmp_cwd / "output" / "average_score_by_grade.png").exists()


def test_file_option_overrides_the_sample(in_tmp_cwd, capsys):
    path = in_tmp_cwd / "mine.csv"
    path.write_text("name,grade,study_hours,attendance,score\nZed,9,1,80,55\n")
    assert main(["--file", str(path), "--no-plots"]) == 0
    out = capsys.readouterr().out
    assert "bundled sample" not in out
    assert "Shape: (1, 5)" in out
    assert "Top scorer: Zed (55)" in out


def test_min_score_option(capsys):
    assert main(["--min-score", "95", "--no-plots"]) == 0
    out = capsys.readouterr().out
    section = out.split("score of 95 or higher ==")[1].split("== Study habits")[0]
    assert "Oliver" in section and "Isabella" in section
    assert "Liam" not in section and "Noah" not in section


def test_missing_file_exits_one_with_a_clear_message(capsys):
    assert main(["--file", "nope.csv"]) == 1
    captured = capsys.readouterr()
    assert "error: File not found: nope.csv" in captured.err
    assert "Traceback" not in captured.err
    assert captured.out == ""


def test_empty_file_exits_one(in_tmp_cwd, capsys):
    (in_tmp_cwd / "empty.csv").write_text("")
    assert main(["--file", "empty.csv"]) == 1
    assert "error:" in capsys.readouterr().err


def test_unwritable_export_dir_exits_one(in_tmp_cwd, capsys):
    (in_tmp_cwd / "blocker").write_text("x")
    assert main(["--no-plots", "--export-dir", "blocker/sub"]) == 1
    assert "Could not write results" in capsys.readouterr().err


def test_export_dir_writes_the_two_csv_files(in_tmp_cwd):
    assert main(["--no-plots", "--export-dir", "results"]) == 0
    saved = pd.read_csv(in_tmp_cwd / "results" / "high_scoring_students.csv")
    assert list(saved.columns) == ["name", "grade", "score"]
    assert len(saved) == 6
    assert (in_tmp_cwd / "results" / "average_scores_by_grade.csv").exists()


def test_no_plots_creates_no_output_folder(in_tmp_cwd):
    assert main(["--no-plots"]) == 0
    assert not (in_tmp_cwd / "output").exists()


def test_plot_dir_option(in_tmp_cwd):
    assert main(["--plot-dir", "charts"]) == 0
    assert (in_tmp_cwd / "charts" / "study_hours_vs_score.png").exists()
    assert not (in_tmp_cwd / "output").exists()


def test_missing_option_drop_on_a_messy_file(in_tmp_cwd, capsys):
    (in_tmp_cwd / "m.csv").write_text(
        "name,grade,study_hours,attendance,score\n"
        "A,9,1,90,60\nB,9,2,91,abc\nC,10,3,92,80\n"
    )
    assert main(["--file", "m.csv", "--missing", "drop", "--no-plots"]) == 0
    assert "Dropped 1 row(s)" in capsys.readouterr().out


@pytest.mark.parametrize(
    "argv",
    [
        ["--missing", "median"],
        ["--min-score", "abc"],
        ["--min-score", "nan"],
        ["--min-score", "inf"],
        ["--show", "--no-plots"],
        ["--unknown-flag"],
    ],
)
def test_invalid_arguments_exit_two(argv, capsys):
    with pytest.raises(SystemExit) as exc:
        main(argv)
    assert exc.value.code == 2
    assert "usage:" in capsys.readouterr().err


def test_help_describes_every_option(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    for flag in ["--file", "--min-score", "--missing", "--export-dir",
                 "--plot-dir", "--show", "--no-plots"]:  # fmt: skip
        assert flag in out


def test_python_dash_m_entry_point_works(in_tmp_cwd):
    completed = subprocess.run(
        [sys.executable, "-m", "data_analyzer", "--no-plots"],
        capture_output=True,
        text=True,
        cwd=in_tmp_cwd,
        timeout=120,
    )
    assert completed.returncode == 0, completed.stderr
    assert "Average: 86.42" in completed.stdout


def test_closed_stdout_pipe_is_not_an_error_with_a_traceback(monkeypatch, capsys):
    silenced = []
    monkeypatch.setattr("data_analyzer.cli._silence_stdout", lambda: silenced.append(1))

    def pipe_closed(*args, **kwargs):
        raise BrokenPipeError

    monkeypatch.setattr("data_analyzer.cli.run_analysis", pipe_closed)
    assert main(["--no-plots"]) == 1
    assert silenced == [1]
    assert "Traceback" not in capsys.readouterr().err


def test_piping_into_a_reader_that_quits_early_is_quiet(in_tmp_cwd):
    child = subprocess.Popen(
        [sys.executable, "-m", "data_analyzer", "--no-plots"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=in_tmp_cwd,
    )
    child.stdout.close()  # the reader leaves before the report is written
    stderr = child.stderr.read()
    child.stderr.close()
    child.wait(timeout=120)
    assert "Traceback" not in stderr
    assert "BrokenPipeError" not in stderr
    assert child.returncode == 1
