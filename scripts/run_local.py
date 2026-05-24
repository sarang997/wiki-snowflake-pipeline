#!/usr/bin/env python3
"""Local runner to exercise fetch and transform steps without Airflow.

Usage:
  python scripts/run_local.py [YYYY-MM-DD] [--load]

By default this will fetch yesterday's data, run transform, and print a summary.
Pass --load to attempt calling `pipeline.load.load(rows)` (requires Snowflake env vars).
"""
import sys
from datetime import date, timedelta
import os

from pipeline.fetch import fetch_data
from pipeline.transform import transform


def main():
    if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
        target = date.fromisoformat(sys.argv[1])
    else:
        target = date.today() - timedelta(days=1)

    do_load = "--load" in sys.argv

    print(f"Running local pipeline for {target}")
    data = fetch_data(target.year, target.month, target.day)
    if data is None:
        print("No data returned by fetch_data()")
        return

    rows = transform(data, target.year, target.month, target.day)
    print(f"Transformed into {len(rows)} rows")
    if len(rows) > 0:
        for r in rows[:5]:
            print(r)

    if do_load:
        # Import here to avoid requiring Snowflake locally during simple tests
        from pipeline.load import load

        missing = [v for v in ("SNOWFLAKE_USER", "SNOWFLAKE_PASSWORD", "SNOWFLAKE_ACCOUNT") if not os.getenv(v)]
        if missing:
            print("Missing Snowflake env vars, cannot load:", missing)
            return
        inserted = load(rows)
        print(f"Inserted {inserted} rows into Snowflake")


if __name__ == "__main__":
    main()
