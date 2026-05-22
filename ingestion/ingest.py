import os
import sys
import time
import logging
import requests
import snowflake.connector
from datetime import date, timedelta

#logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("wiki_pipeline.log"),
    ],
)
log = logging.getLogger(__name__)

#configuration
def get_snowflake_config() -> dict:
    required_vars = ["SNOWFLAKE_USER", "SNOWFLAKE_PASSWORD", "SNOWFLAKE_ACCOUNT"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        missing = ", ".join(missing_vars)
        raise RuntimeError(f"Missing required Snowflake environment variables: {missing}")

    config = {
        "user": os.environ["SNOWFLAKE_USER"],
        "password": os.environ["SNOWFLAKE_PASSWORD"],
        "account": os.environ["SNOWFLAKE_ACCOUNT"],
    }

    for env_name, config_name in [
        ("SNOWFLAKE_ROLE", "role"),
        ("SNOWFLAKE_WAREHOUSE", "warehouse"),
        ("SNOWFLAKE_DATABASE", "database"),
    ]:
        value = os.getenv(env_name)
        if value:
            config[config_name] = value

    return config

BATCH_SIZE    = 500
MAX_RETRIES   = 3
RETRY_BACKOFF = 5
REQUEST_DELAY = 0.5

#connecting to snowflake
def get_connection():
    conn = snowflake.connector.connect(**get_snowflake_config())
    cursor = conn.cursor()
    database_name = os.getenv("SNOWFLAKE_DATABASE", "WIKIPEDIA")
    cursor.execute(f"USE DATABASE {database_name}")
    return conn, cursor


#fetching data
def fetch_data(year: int, month: int, day: int) -> dict | None:
    url = (
        f"https://wikimedia.org/api/rest_v1/metrics/pageviews/top/"
        f"en.wikipedia/all-access/{year}/{month:02d}/{day:02d}"
    )
    headers = {"User-Agent": "wiki-pipeline-project/1.0"}

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, headers=headers, timeout=15)

            if response.status_code == 200:
                return response.json()

            if response.status_code == 404:
                # Data genuinely missing for this date (future date, outage, etc.)
                log.warning(f"No data available for {year}-{month:02d}-{day:02d} (404) – skipping.")
                return None

            # Transient errors – retry
            log.warning(
                f"HTTP {response.status_code} for {year}-{month:02d}-{day:02d} "
                f"(attempt {attempt}/{MAX_RETRIES})"
            )

        except requests.RequestException as e:
            log.warning(f"Request error for {year}-{month:02d}-{day:02d}: {e} (attempt {attempt}/{MAX_RETRIES})")

        if attempt < MAX_RETRIES:
            sleep_time = RETRY_BACKOFF * (2 ** (attempt - 1))
            log.info(f"Retrying in {sleep_time}s…")
            time.sleep(sleep_time)

    log.error(f"All {MAX_RETRIES} attempts failed for {year}-{month:02d}-{day:02d} – skipping.")
    return None

#transforming data
def transform(data: dict, year: int, month: int, day: int) -> list[tuple]:
    try:
        articles = data["items"][0]["articles"]
    except (KeyError, IndexError) as e:
        log.error(f"Unexpected payload structure: {e}")
        return []

    page_date = date(year, month, day).isoformat()  # store as DATE string
    rows = [
        (page_date, article["article"], article["views"], article["rank"])
        for article in articles
    ]
    return rows

#loading data to snowflake
def load_batch(cursor, rows: list[tuple]) -> int:
    """Insert rows in chunks of BATCH_SIZE. Returns total rows inserted."""
    total = 0
    for i in range(0, len(rows), BATCH_SIZE):
        chunk = rows[i : i + BATCH_SIZE]
        cursor.executemany(
            """
            INSERT INTO wiki_pageviews (page_date, article, views, rank)
            VALUES (%s, %s, %s, %s)
            """,
            chunk,
        )
        total += len(chunk)
    return total


def truncate_table(cursor, conn):
    log.info("Truncating wiki_pageviews table…")
    cursor.execute("TRUNCATE TABLE wiki_pageviews")
    conn.commit()
    log.info("Table truncated.")

#pipeline
def run():
    # Default to yesterday, but allow override: python ingest.py 2026-01-15
    if len(sys.argv) > 1:
        target_date = date.fromisoformat(sys.argv[1])
    else:
        target_date = date.today() - timedelta(days=1)

    log.info(f"Fetching data for {target_date}")

    conn, cursor = get_connection()

    # Delete just that day's data (idempotent — safe to rerun)
    cursor.execute(
        "DELETE FROM wiki_pageviews WHERE page_date = %s",
        (target_date.isoformat(),)
    )
    conn.commit()

    data = fetch_data(target_date.year, target_date.month, target_date.day)
    if data is None:
        log.error("No data returned — exiting.")
        return

    rows = transform(data, target_date.year, target_date.month, target_date.day)
    inserted = load_batch(cursor, rows)
    conn.commit()

    log.info(f"Done. Inserted {inserted} rows for {target_date}.")
    cursor.close()
    conn.close()

if __name__ == "__main__":
    run()