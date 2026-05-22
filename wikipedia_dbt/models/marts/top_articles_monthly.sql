-- models/marts/top_articles_monthly.sql
WITH base AS (
    SELECT * FROM {{ ref('stg_wiki_pageviews') }}
)

SELECT
    month_start,
    year,
    month,
    article_name,
    SUM(views)                                      AS total_views,
    ROUND(AVG(views), 0)                            AS avg_daily_views,
    MIN(rank)                                       AS best_rank,
    COUNT(DISTINCT page_date)                       AS days_in_top_1000,
    ROW_NUMBER() OVER (
        PARTITION BY month_start
        ORDER BY SUM(views) DESC
    )                                               AS monthly_rank

FROM base
GROUP BY month_start, year, month, article_name
QUALIFY monthly_rank <= 20
ORDER BY month_start, monthly_rank