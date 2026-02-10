# Stack Exchange Data Pipeline - Lab 2

This project implements an advanced data pipeline that fetches top posts from Stack Exchange API, encodes them in AVRO format, and stores them in GCS and BigQuery with schema validation and dead-letter queue handling.

## Architecture

```
Stack Exchange API → Producer (AVRO) → Pub/Sub (with Schema) → Consumer → GCS (JSON/Parquet) → BigQuery
                                      ↓
                              Dead-Letter Topic (invalid messages)
```

## Components

- **Producer**: Fetches top posts from Stack Exchange API, encodes them in AVRO, and publishes to Pub/Sub
- **Consumer**: Pull-based subscriber that decodes AVRO messages and stores them in GCS/BigQuery
- **Schema Registry**: AVRO schema validation for message consistency
- **Dead-Letter Queue**: Handles invalid messages automatically

## Prerequisites

- Google Cloud SDK
- Docker
- Access to Google Cloud Project
- Configured gcloud authentication
- Stack Exchange API key (stored in Secret Manager)

## GCP Resources Required

1. **Pub/Sub**:
   - Main topic with AVRO schema attached
   - Dead-letter topic for invalid messages
   - Subscription with schema validation enabled

2. **Storage**:
   - GCS bucket for JSON and Parquet files
   - BigQuery dataset and table

3. **Secrets**:
   - `STACK_EXCHANGE_API_KEY` in Secret Manager

## Local Development

1. Install dependencies:
```bash
# Producer
pip install -r producer/requirements.txt

# Consumer
pip install -r consumer/requirements.txt
```

2. Set up environment variables:
```bash
# Producer
export PROJECT_ID=your-project-id
export PUBSUB_TOPIC=lab1-topic
export DLQ_TOPIC_ID=deadletter

# Consumer
export PROJECT_ID=your-project-id
export PUBSUB_SUBSCRIPTION=lab1-subscription
export GCS_BUCKET=lab1-stackex-data
export BIGQUERY_DATASET=stackex_data
export BIGQUERY_TABLE=posts
```

3. Run locally:
```bash
# Producer (one-time execution)
python producer/main.py

# Consumer (continuous listening)
python consumer/main.py
```

## Docker Deployment

1. Build the Docker images:
```bash
# Build producer
cd producer
docker build -t lab1-producer .

# Build consumer
cd ../consumer
docker build -t lab1-consumer .
```

2. Run with Docker:
```bash
# Producer
docker run --rm \
  -v $HOME/.config/gcloud:/root/.config/gcloud \
  -e PROJECT_ID=your-project-id \
  -e PUBSUB_TOPIC=lab1-topic \
  -e DLQ_TOPIC_ID=deadletter \
  lab1-producer

# Consumer
docker run --rm \
  -v $HOME/.config/gcloud:/root/.config/gcloud \
  -e PROJECT_ID=your-project-id \
  -e PUBSUB_SUBSCRIPTION=lab1-subscription \
  -e GCS_BUCKET=lab1-stackex-data \
  -e BIGQUERY_DATASET=stackex_data \
  -e BIGQUERY_TABLE=posts \
  lab1-consumer
```

## Cloud Run Deployment

### Producer (Cloud Run Job)
```bash
# Deploy producer job
gcloud run jobs deploy stackex-producer-job \
  --source producer \
  --env-vars-file .env.yaml \
  --region europe-west8

# Execute the job
gcloud run jobs execute stackex-producer-job --region europe-west8
```

### Consumer (Cloud Run Service)
```bash
# Deploy consumer service
gcloud run deploy stackex-consumer \
  --source consumer \
  --env-vars-file consumer/.env.yaml \
  --region europe-west8 \
  --min-instances 1
```

## CI/CD Pipeline

The project includes automated CI/CD using GitHub Actions:

- **CI Workflow** (`.github/workflows/ci.yaml`):
  - Runs on pull requests
  - Linting with pylint
  - EditorConfig validation
  - Docker build tests

- **CD Workflow** (`.github/workflows/cd.yaml`):
  - Runs on push to main branch
  - Builds and pushes Docker images
  - Deploys to Cloud Run
  - Executes producer job

## Data Flow

1. **Producer**:
   - Fetches top 10 posts from Stack Exchange API
   - Transforms data to match AVRO schema
   - Encodes messages in AVRO binary format
   - Publishes to main topic (valid) or DLQ (invalid)

2. **Consumer**:
   - Pulls messages from Pub/Sub subscription
   - Decodes AVRO messages
   - Stores as JSON in GCS (`json/{message_id}.json`)
   - Stores as Parquet in GCS with time partitioning (`parquet/year=.../month=.../day=.../hour=.../`)
   - Loads Parquet files into BigQuery

## Error Handling

- **Schema Validation**: Invalid messages automatically routed to DLQ
- **Processing Errors**: Runtime errors trigger message retry via `nack()`
- **Negative Test**: Producer deliberately breaks last message to test DLQ

## Monitoring

Check Cloud Run logs for monitoring:
```bash
# Producer logs
gcloud logs read "resource.type=cloud_run_revision" \
  --resource-names="projects/your-project-id/locations/europe-west8/services/stackex-producer-job"

# Consumer logs
gcloud logs read "resource.type=cloud_run_revision" \
  --resource-names="projects/your-project-id/locations/europe-west8/services/stackex-consumer"
```