#transforming data
import logging 
from datetime import date

log = logging.getLogger(__name__)

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