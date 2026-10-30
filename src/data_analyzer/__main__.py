"""Allow ``python -m data_analyzer`` as an alternative to the ``analyzer`` command."""

import sys

from data_analyzer.cli import main

if __name__ == "__main__":
    sys.exit(main())
