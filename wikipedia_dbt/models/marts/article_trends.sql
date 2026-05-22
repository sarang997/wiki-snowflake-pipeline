-- models/marts/article_trends.sql
WITH base AS (
    SELECT * FROM {{ ref('stg_wiki_pageviews') }}
),

with_lag AS (
    SELECT
        page_date,
        article_name,
        views,
        rank,

        -- previous day stats
        LAG(views) OVER (
            PARTITION BY article_name ORDER BY page_date
        )                                           AS prev_views,

        LAG(rank) OVER (
            PARTITION BY article_name ORDER BY page_date
        )                                           AS prev_rank

    FROM base
)

SELECT
    page_date,
    article_name,
    views,
    rank,
    prev_views,
    prev_rank,

    -- change metrics
    views - prev_views                              AS views_change,
    prev_rank - rank                                AS rank_improvement, -- positive = moved up
    ROUND((views - prev_views) * 100.0 /
        NULLIF(prev_views, 0), 2)                   AS views_pct_change,

    CASE
        WHEN prev_rank IS NULL      THEN 'new_entry'
        WHEN rank < prev_rank       THEN 'rising'
        WHEN rank > prev_rank       THEN 'falling'
        ELSE                             'stable'
    END                                             AS trend

FROM with_lag
ORDER BY page_date, rank