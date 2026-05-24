from pipeline.config import BATCH_SIZE
import snowflake.connector
import os
from dotenv import load_dotenv

# Load .env file (if present) so local runs pick up credentials from .env
load_dotenv()

# configuration
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

#connecting to snowflake
def get_connection():
    conn = snowflake.connector.connect(**get_snowflake_config())
    cursor = conn.cursor()
    database_name = os.getenv("SNOWFLAKE_DATABASE", "WIKIPEDIA")
    cursor.execute(f"USE DATABASE {database_name}")
    return conn, cursor



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


def load(rows: list[tuple]) -> int:
    """Top-level helper used by the DAG: opens a connection, writes rows, commits and closes."""
    if not rows:
        return 0
    conn, cursor = get_connection()
    try:
        total = load_batch(cursor, rows)
        conn.commit()
        return total
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass