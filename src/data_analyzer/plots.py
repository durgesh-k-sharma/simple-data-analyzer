"""Charts from the tutorial: a scatter plot and a bar chart.

Plots are always saved as PNG files. A window is opened only when ``show`` is
true, so the default run works on servers and in CI without a display.
"""

from collections.abc import Sequence
from pathlib import Path
from typing import Literal

import pandas as pd

from data_analyzer.schema import GRADE, SCORE, STUDY_HOURS
from data_analyzer.stats import average_by_grade

PlotKind = Literal["scatter", "bar"]
FIGURE_SIZE = (7, 4.5)

FILENAMES: dict[PlotKind, str] = {
    "scatter": "study_hours_vs_score.png",
    "bar": "average_score_by_grade.png",
}


def has_scatter_data(data: pd.DataFrame) -> bool:
    """True if at least one row has both study hours and a score."""
    return not data[[STUDY_HOURS, SCORE]].dropna().empty


def has_bar_data(data: pd.DataFrame) -> bool:
    """True if at least one row has both a grade and a score."""
    return not data[[GRADE, SCORE]].dropna().empty


def render_plots(
    data: pd.DataFrame,
    kinds: Sequence[PlotKind],
    plot_dir: Path,
    *,
    show: bool = False,
) -> list[Path]:
    """Draw the requested plots, save each as a PNG and optionally display them.

    Without ``show`` the figures are built with matplotlib's object-oriented API
    and never touch pyplot, so calling this does not change the process-wide
    matplotlib backend or need a display.

    Args:
        data: Data containing the columns each plot needs.
        kinds: Which plots to draw, from ``"scatter"`` and ``"bar"``.
        plot_dir: Directory for the PNG files; created if it does not exist.
        show: Also open an interactive window (blocks until it is closed).

    Returns:
        The paths of the PNG files written.

    Raises:
        OSError: If the directory or a file cannot be written.
    """
    plot_dir.mkdir(parents=True, exist_ok=True)

    figures = []
    paths: list[Path] = []
    try:
        for kind in kinds:
            fig, ax = _new_figure(show)
            figures.append(fig)
            if kind == "scatter":
                _draw_scatter(ax, data)
            else:
                _draw_bar(ax, data)
            fig.tight_layout()
            path = plot_dir / FILENAMES[kind]
            fig.savefig(path, dpi=150)
            paths.append(path)
        if show:
            _pyplot().show()
    finally:
        if show:
            plt = _pyplot()
            for fig in figures:
                plt.close(fig)
    return paths


def _pyplot():
    import matplotlib.pyplot as plt

    return plt


def _new_figure(show: bool):
    """Create a figure and axes; only windowed figures go through pyplot."""
    if show:
        return _pyplot().subplots(figsize=FIGURE_SIZE)
    from matplotlib.figure import Figure

    fig = Figure(figsize=FIGURE_SIZE)
    return fig, fig.subplots()


def _draw_scatter(ax, data: pd.DataFrame) -> None:
    ax.scatter(data[STUDY_HOURS], data[SCORE])
    ax.set_xlabel("Study Hours")
    ax.set_ylabel("Test Score")
    ax.set_title("Study Hours vs. Test Scores")


def _draw_bar(ax, data: pd.DataFrame) -> None:
    averages = average_by_grade(data)
    ax.bar(averages.index.astype(str), averages.to_numpy())
    ax.set_xlabel("Grade")
    ax.set_ylabel("Average Score")
    ax.set_title("Average Score by Grade")
