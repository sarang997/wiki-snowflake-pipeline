-- models/staging/stg_wiki_pageviews.sql
-- Cleans and standardises raw Wikipedia pageview data

WITH source AS (
    SELECT * FROM {{ source('raw', 'wiki_pageviews') }}
),

cleaned AS (
    SELECT
        page_date,
        REPLACE(article, '_', ' ')          AS article_name,
        article                             AS article_raw,
        views,
        rank,

        -- useful derived columns
        YEAR(page_date)                     AS year,
        MONTH(page_date)                    AS month,
        DAYOFWEEK(page_date)                AS day_of_week,
        DATE_TRUNC('month', page_date)      AS month_start

    FROM source
    WHERE
        -- filter out Wikimedia noise
        article NOT IN ('Main_Page', 'Special:Search', '-')
        AND views > 0
        AND page_date IS NOT NULL
)

SELECT * FROM cleaned