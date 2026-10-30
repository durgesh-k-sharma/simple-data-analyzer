"""Exceptions raised by the analyzer for expected, user-facing failures."""


class AnalyzerError(Exception):
    """An expected failure (bad file, empty data, unwritable output).

    The command-line interface catches this, prints the message to stderr and
    exits with status 1. Anything else is a bug and surfaces as a traceback.
    """
