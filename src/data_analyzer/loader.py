"""Loading CSV files, including the bundled sample dataset."""

from importlib.resources import as_file, files
from pathlib import Path

import pandas as pd

from data_analyzer.errors import AnalyzerError

SAMPLE_DATASET_NAME = "students.csv"


def load_csv(path: Path) -> pd.DataFrame:
    """Read a CSV file into a DataFrame.

    Args:
        path: Location of the CSV file.

    Returns:
        A DataFrame with at least one data row.

    Raises:
        AnalyzerError: If the file is missing, unreadable, empty, not valid
            CSV, or has a header but no data rows.
    """
    try:
        data = pd.read_csv(path)
    except FileNotFoundError:
        raise AnalyzerError(f"File not found: {path}") from None
    except pd.errors.EmptyDataError:
        raise AnalyzerError(f"{path} is empty (no header or data).") from None
    except (pd.errors.ParserError, UnicodeDecodeError) as exc:
        raise AnalyzerError(f"Could not parse {path} as CSV: {exc}") from exc
    except OSError as exc:
        reason = exc.strerror or str(exc)
        raise AnalyzerError(f"Cannot read {path}: {reason}") from exc

    if data.empty:
        raise AnalyzerError(f"{path} has a header but no data rows.")
    return data


def load_sample_dataset() -> pd.DataFrame:
    """Load the 12-row student dataset bundled with the package."""
    resource = files("data_analyzer").joinpath("data", SAMPLE_DATASET_NAME)
    with as_file(resource) as path:
        return load_csv(path)
