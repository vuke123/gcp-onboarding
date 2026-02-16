{{ config(materialized='view') }}

SELECT *
FROM `{{ target.project }}.{{ target.dataset }}.posts`
