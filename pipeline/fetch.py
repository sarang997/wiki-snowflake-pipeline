from pipeline.config import MAX_RETRIES, RETRY_BACKOFF
import requests
import logging
import time

log = logging.getLogger(__name__)
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