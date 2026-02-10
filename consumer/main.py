"""Pub/Sub consumer service that processes messages from a subscription."""

"""Consumer service that processes AVRO messages from Pub/Sub and stores them in GCS/BigQuery."""

import io
import json
import os
from datetime import datetime
from pathlib import Path

import fastavro
import pandas as pd
from google.cloud import bigquery
from google.cloud import pubsub_v1
from google.cloud import storage
from google.cloud import secretmanager

from schema import STACKEX_POST_SCHEMA

# Load config from env
PROJECT_ID = os.environ["PROJECT_ID"]
SUBSCRIPTION_ID = os.environ["PUBSUB_SUBSCRIPTION"]
BUCKET_NAME = os.environ["GCS_BUCKET"]
DATASET_ID = os.environ["BIGQUERY_DATASET"]
TABLE_ID = os.environ["BIGQUERY_TABLE"]

# Initialize clients
storage_client = storage.Client()
bq_client = bigquery.Client()
bucket = storage_client.bucket(BUCKET_NAME)

# Parse AVRO schema once
parsed_schema = fastavro.parse_schema(STACKEX_POST_SCHEMA)


def get_secret(secret_id: str) -> str:
    """Retrieve a secret from Google Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")


def store_json(message_id: str, data: dict) -> None:
    """Store message as JSON in GCS."""
    blob = bucket.blob(f"json/{message_id}.json")
    blob.upload_from_string(
        json.dumps(data, ensure_ascii=False),
        content_type="application/json"
    )


def store_parquet(data: dict) -> str:
    """Store message as Parquet in GCS with time-based partitioning."""
    # Convert to DataFrame
    df = pd.DataFrame([data])

    # Extract timestamp components
    ts = datetime.fromtimestamp(data["creation_date"])
    partition_path = f"year={ts.year}/month={ts.month:02d}/day={ts.day:02d}/hour={ts.hour:02d}"
    
    # Create full path including partition
    full_path = f"parquet/{partition_path}/part-{data['question_id']:08d}.parquet"
    
    # Upload to GCS
    blob = bucket.blob(full_path)
    buffer = io.BytesIO()
    df.to_parquet(buffer, engine="pyarrow")
    blob.upload_from_file(
        buffer,
        rewind=True,
        content_type="application/octet-stream"
    )
    
    return f"gs://{BUCKET_NAME}/{full_path}"


def load_to_bigquery(parquet_path: str) -> None:
    """Load Parquet file into BigQuery."""
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        schema_update_options=[
            bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION
        ]
    )
    
    load_job = bq_client.load_table_from_uri(
        parquet_path,
        table_ref,
        job_config=job_config
    )
    load_job.result()  # Wait for completion


def process_message(message: pubsub_v1.subscriber.message.Message) -> None:
    """Process a single message from Pub/Sub."""
    try:
        # Decode AVRO
        decoded = fastavro.schemaless_reader(
            io.BytesIO(message.data),
            parsed_schema
        )
        
        print(f"[consumer] processing message {message.message_id}")
        
        # Store as JSON
        store_json(message.message_id, decoded)
        print(f"[consumer] stored JSON: {message.message_id}.json")
        
        # Store as Parquet
        parquet_path = store_parquet(decoded)
        print(f"[consumer] stored Parquet: {parquet_path}")
        
        # Load to BigQuery
        #load_to_bigquery(parquet_path)
        print(f"[consumer] loaded to BigQuery: {message.message_id}")
        
        # Acknowledge the message
        message.ack()
        print(f"[consumer] acknowledged message: {message.message_id}")
        
    except Exception as e:
        print(f"[consumer] error processing message {message.message_id}: {e}")
        message.nack()  # Retry the message


def main() -> None:
    """Main function that sets up the subscriber."""
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(
        PROJECT_ID,
        SUBSCRIPTION_ID
    )
    
    print(f"[consumer] listening on {subscription_path}...")
    
    future = subscriber.subscribe(
        subscription_path,
        callback=process_message
    )
    
    try:
        future.result()  # Block until the future completes
    except KeyboardInterrupt:
        future.cancel()
        print("\n[consumer] stopped.")


if __name__ == "__main__":
    main()
