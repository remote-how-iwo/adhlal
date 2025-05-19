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
    parser.add_argument("input_csv", help="Input chat export CSV file")
    parser.add_argument("--output-csv", help="Output CSV file for structured results", default=None)
    args = parser.parse_args()

    patch_windows_event_loop()
    asyncio.run(etl_main(Path(args.input_csv), args.output_csv))

if __name__ == "__main__":
    main() 