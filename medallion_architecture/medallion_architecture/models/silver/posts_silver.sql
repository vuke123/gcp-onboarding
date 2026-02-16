{{ config(
  materialized='table',
  partition_by={
    "field": "created_ts",
    "data_type": "timestamp",
    "granularity": "day"
  },
  cluster_by=["sentiment"]
) }}

WITH deduplicated AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY question_id
      ORDER BY creation_date DESC
    ) AS rn
  FROM {{ ref('posts_bronze') }}
)

SELECT
  question_id,

  -- title cleaning: TRIM + remove special chars + collapse whitespace
  TRIM(
    REGEXP_REPLACE(
      REGEXP_REPLACE(COALESCE(title, ''), r'[^A-Za-z0-9\s]+', ' '),
      r'\s+',
      ' '
    )
  ) AS title_clean,

  -- author (if owner is present as a RECORD)
  owner.display_name AS author,

  COALESCE(score, 0) AS score_filled,
  COALESCE(answer_count, 0) AS answer_count_filled,
  COALESCE(view_count, 0) AS view_count_filled,

  link,
  creation_date,

  -- convert epoch seconds -> TIMESTAMP
  TIMESTAMP_SECONDS(CAST(creation_date AS INT64)) AS created_ts,

  CASE
    WHEN COALESCE(score, 0) >= 50 AND COALESCE(answer_count, 0) >= 10 THEN 'HIGH_ENGAGEMENT'
    WHEN COALESCE(score, 0) >= 20 THEN 'POSITIVE'
    WHEN COALESCE(score, 0) < 0 THEN 'NEGATIVE'
    ELSE 'NEUTRAL'
  END AS sentiment

FROM deduplicated
WHERE rn = 1
  AND title IS NOT NULL
  AND LENGTH(TRIM(title)) > 0
