{{ config(
  materialized='table',
  partition_by={
    "field": "report_date",
    "data_type": "date"
  },
  cluster_by=["sentiment"]
) }}

WITH daily_aggregates AS (
  SELECT
    DATE(created_ts) AS report_date,
    sentiment,
    COUNT(*) AS post_count,
    AVG(score_filled) AS avg_score,
    SUM(score_filled) AS total_score,
    COUNT(DISTINCT author) AS unique_authors
  FROM {{ ref('posts_silver') }}
  GROUP BY report_date, sentiment
),

window_calculations AS (
  SELECT
    *,
    SUM(post_count) OVER (
      PARTITION BY sentiment
      ORDER BY report_date
      ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS posts_rolling_7d,
    LAG(post_count) OVER (
      PARTITION BY sentiment
      ORDER BY report_date
    ) AS prev_day_posts
  FROM daily_aggregates
)

SELECT
  *,
  CASE
    WHEN prev_day_posts > 0 THEN ((post_count - prev_day_posts) / prev_day_posts) * 100
    ELSE NULL
  END AS day_over_day_change_pct
FROM window_calculations
