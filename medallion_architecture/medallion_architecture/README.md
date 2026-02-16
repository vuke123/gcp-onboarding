# BigQuery Medallion Analytics (dbt + Great Expectations + Looker Studio)

Analytics layer implementation on top of BigQuery raw table using medallion architecture (bronze → silver → gold). The solution includes data quality validation using Great Expectations and visualization layer in Looker Studio.

## Architecture

- **Bronze**: Raw data exposure (view over the raw table)
- **Silver**: Cleaned + standardized + deduplicated table (partitioned, clustered)
- **Gold**: Business-ready aggregated table for dashboards (partitioned, clustered)

## Prerequisites

- Python + pip
- gcloud + bq CLI configured
- BigQuery dataset with raw table
- dbt BigQuery adapter + Great Expectations

## GCP Setup

1. Configure authentication:
```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project ${PROJECT_ID}
```

2. Create BigQuery dataset:
```bash
bq mk --dataset \
    --description "Stack Exchange Data" \
    --location=EU \
    ${PROJECT_ID}:stackex_data
```

3. Configure dbt profile in `~/.dbt/profiles.yml`:
```yaml
medallion_architecture:
  target: dev
  outputs:
    dev:
      type: bigquery
      method: oauth
      project: ${PROJECT_ID}
      dataset: stackex_data
      location: EU
      threads: 4
```

4. Configure Great Expectations in `great_expectations/uncommitted/config_variables.yml`:
```yaml
GCP_PROJECT: ${PROJECT_ID}
```

### Install Dependencies

```bash
pip install dbt-bigquery
pip install great_expectations==0.15.42
```

## Project Setup

### 0. Verify GCP Project / Dataset / Tables

```bash
gcloud config get-value project
bq ls --project_id=$(gcloud config get-value project)
bq ls $(gcloud config get-value project):<DATASET>
```

## Task 1 — Build Bronze, Silver, Gold + Data Quality

### 1. Initialize dbt Project

```bash
dbt init medallion_architecture
cd medallion_architecture
```

During initialization, configure:
- adapter: bigquery
- auth: oauth (recommended)
- project: GCP project id
- dataset: existing BigQuery dataset
- location: choose the correct location for your dataset (e.g. EU/US)

Your dbt profile will be created under: `~/.dbt/profiles.yml`

### 2. Project Structure

```bash
rm -rf models/example
mkdir -p models/bronze models/silver models/gold
```

### Bronze Model (View)

1. Create `models/bronze/posts_bronze.sql`:

```sql
{{ config(materialized='view') }}
SELECT *
FROM `${project}.${dataset}.raw_posts`
```

2. Run:
```bash
dbt run --select posts_bronze
```

### Silver Model (Clean + Dedupe + Sentiment)

1. Create `models/silver/posts_silver.sql`

Key requirements:
- Deduplicate with ROW_NUMBER() by id (keep newest)
- Clean title via regex + TRIM
- Fill NULLs with COALESCE
- Derive sentiment via CASE
- Partition by day (timestamp/date field) and cluster (e.g. sentiment)

Example config:
```sql
{{ config(
  materialized='table',
  partition_by={"field": "created_ts", "data_type": "timestamp", "granularity": "day"},
  cluster_by=["sentiment"]
) }}
```

2. Add documentation + tests in `models/silver/posts_silver.yml` (unique/not_null)

3. Run and test:
```bash
dbt run --select posts_silver
dbt test --select posts_silver
```

### Gold Model (Aggregations + Windows)

1. Create `models/gold/posts_gold.sql`

Requirements:
- Daily aggregates by report_date and sentiment
- 7-day rolling sum (ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)
- Previous day value via LAG
- Day-over-day percent change with division-by-zero protection
- Partition by report_date (date), cluster by sentiment

Example config:
```sql
{{ config(
  materialized='table',
  partition_by={"field": "report_date", "data_type": "date"},
  cluster_by=["sentiment"]
) }}
```

2. Run:
```bash
dbt run --select posts_gold
```

### Data Quality — Great Expectations

1. Initialize GE in the dbt project folder:
```bash
great_expectations init
```

2. Create a datasource (SQL → BigQuery):
```bash
great_expectations datasource new
```

Connection string example:
```python
connection_string = "bigquery://${project}/${dataset}?key_path=~/.config/gcloud/application_default_credentials.json"
schema_name = "${dataset}"
table_name = "posts_bronze"  # or another dbt model to validate
```

3. Create suites:
```bash
great_expectations suite new
```

Recommended expectations:
- Bronze: schema drift/monitoring (column exists), uniqueness, row count, allowed NULL ratio
- Silver: uniqueness, not null for critical fields, string length bounds

4. Create & run checkpoints:
```bash
great_expectations checkpoint run bronze_checkpoint
great_expectations checkpoint run silver_checkpoint
```

### dbt Documentation
```bash
dbt docs generate
dbt docs serve
```

## Task 2 — Looker Studio Dashboard

### 1. Create Report + Connect BigQuery

1. Open Looker Studio
2. Create New Report
3. Add data → BigQuery
4. Select:
   - Project → Dataset → posts_gold
   - Use Live Connection for real-time data

### 2. Required Visualization: Sentiment Trend Over Time

Add a Time series / Line chart:
- Dimension (X axis): report_date
- Metric (Y axis): post_count
- Breakdown dimension: sentiment

### 3. Add Controls

1. Date Range Control (for partition pruning + cost):
   - Control → Date range control
   - Use report_date as the date field

2. Optional: Add sentiment dropdown filter

### 4. Save and Verify

1. Test date range updates
2. Confirm Live vs Extract behavior (Live recommended)

## Useful Commands

### dbt Commands
```bash
dbt run
dbt test
dbt build
dbt docs generate
dbt docs serve
```

### BigQuery Checks
```bash
bq ls <PROJECT_ID>:<DATASET>
bq show --schema <PROJECT_ID>:<DATASET>.<TABLE>
bq head -n 20 <PROJECT_ID>:<DATASET>.<TABLE>
```
