import subprocess
import sys

import matplotlib.pyplot as plt
import numpy as np
import pytest

from data_analyzer import plots

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def test_render_writes_both_png_files(sample, tmp_path):
    paths = plots.render_plots(sample, ["scatter", "bar"], tmp_path)
    assert [p.name for p in paths] == [
        "study_hours_vs_score.png",
        "average_score_by_grade.png",
    ]
    for path in paths:
        assert path.read_bytes().startswith(PNG_SIGNATURE)
        assert path.stat().st_size > 1000


def test_render_creates_missing_directories(sample, tmp_path):
    target = tmp_path / "a" / "b"
    plots.render_plots(sample, ["bar"], target)
    assert (target / "average_score_by_grade.png").exists()


def test_render_only_draws_requested_kinds(sample, tmp_path):
    paths = plots.render_plots(sample, ["scatter"], tmp_path)
    assert [p.name for p in paths] == ["study_hours_vs_score.png"]
    assert not (tmp_path / "average_score_by_grade.png").exists()


def test_figures_are_closed_after_rendering(sample, tmp_path):
    plots.render_plots(sample, ["scatter", "bar"], tmp_path)
    assert plt.get_fignums() == []


def test_show_opens_windows_once_and_still_saves(sample, tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(plt, "show", lambda: calls.append("show"))
    paths = plots.render_plots(sample, ["scatter", "bar"], tmp_path, show=True)
    assert calls == ["show"]
    assert len(paths) == 2 and all(p.exists() for p in paths)
    assert plt.get_fignums() == []


def test_show_is_not_called_by_default(sample, tmp_path, monkeypatch):
    monkeypatch.setattr(plt, "show", lambda: pytest.fail("show() must not be called"))
    plots.render_plots(sample, ["scatter"], tmp_path)


def test_unwritable_directory_raises_oserror(sample, tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("x")
    with pytest.raises(OSError):
        plots.render_plots(sample, ["bar"], blocker / "sub")


def test_figures_are_closed_even_when_saving_fails(sample, tmp_path, monkeypatch):
    def boom(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr("matplotlib.figure.Figure.savefig", boom)
    with pytest.raises(OSError, match="disk full"):
        plots.render_plots(sample, ["scatter"], tmp_path)
    assert plt.get_fignums() == []


def test_data_availability_checks(sample):
    assert plots.has_scatter_data(sample)
    assert plots.has_bar_data(sample)
    sample["score"] = np.nan
    assert not plots.has_scatter_data(sample)
    assert not plots.has_bar_data(sample)


def test_file_only_rendering_does_not_import_pyplot(tmp_path):
    """Saving PNGs must not switch the process-wide matplotlib backend."""
    script = (
        "import sys\n"
        "from pathlib import Path\n"
        "from data_analyzer.loader import load_sample_dataset\n"
        "from data_analyzer.plots import render_plots\n"
        "data = load_sample_dataset()\n"
        f"paths = render_plots(data, ['scatter', 'bar'], Path(r'{tmp_path}'))\n"
        "assert len(paths) == 2 and all(p.exists() for p in paths)\n"
        "print('pyplot' if 'matplotlib.pyplot' in sys.modules else 'clean')\n"
    )
    done = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, timeout=120
    )
    assert done.returncode == 0, done.stderr
    assert done.stdout.strip() == "clean"
