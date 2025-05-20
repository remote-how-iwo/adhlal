"""Allows `python -m etl data.csv` and CLI entry point."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
import argparse

from etl import main as etl_main
from etl.helpers.windows_loop import patch_windows_event_loop

def main():
    parser = argparse.ArgumentParser(description="Run Adhlal ETL pipeline.")
    parser.add_argument("input_csv", help="Input chat export CSV file (e.g., data/chats.csv)")
    parser.add_argument(
        "--config",
        default="src/etl/configs/student.yml",
        help=(
            "Path to the YAML configuration file for the survey type. "
            "(default: %(default)s for student survey). "
            "Example for employer survey: --config src/etl/configs/employer.yml"
        )
    )
    parser.add_argument(
        "--output-csv", 
        help="Output CSV file for structured results (e.g., output/structured_data.csv)", 
        default=None
    )
    args = parser.parse_args()

    patch_windows_event_loop()
    asyncio.run(etl_main(Path(args.input_csv), Path(args.config), args.output_csv))

if __name__ == "__main__":
    main() 