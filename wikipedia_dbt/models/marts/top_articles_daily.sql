-- models/marts/top_articles_daily.sql
WITH base AS (
    SELECT * FROM {{ ref('stg_wiki_pageviews') }}
)

SELECT
    page_date,
    article_name,
    views,
    rank,

    -- how many views vs the #1 article that day
    MAX(views) OVER (PARTITION BY page_date)        AS top_views_that_day,
    ROUND(views * 100.0 /
        MAX(views) OVER (PARTITION BY page_date), 2) AS pct_of_top

FROM base
WHERE rank <= 10
ORDER BY page_date, rank