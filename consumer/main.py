"""Pub/Sub consumer service that processes messages from a subscription."""

"""Consumer service that processes AVRO messages from Pub/Sub push and stores them in GCS/BigQuery."""

import base64
import io
import json
import os
from datetime import datetime

import fastavro
import pandas as pd
from flask import Flask, request
from google.cloud import bigquery
from google.cloud import storage

from schema import STACKEX_POST_SCHEMA

app = Flask(__name__)

# Load config from env
PROJECT_ID = os.environ["PROJECT_ID"]
BUCKET_NAME = os.environ["GCS_BUCKET"]
DATASET_ID = os.environ["BIGQUERY_DATASET"]
TABLE_ID = os.environ["BIGQUERY_TABLE"]

# Initialize clients
storage_client = storage.Client()
bq_client = bigquery.Client()
bucket = storage_client.bucket(BUCKET_NAME)

# Parse AVRO schema once
parsed_schema = fastavro.parse_schema(STACKEX_POST_SCHEMA)


@app.get("/")
def health():
    """Health check endpoint required by Cloud Run."""
    return "OK", 200


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


@app.post("/pubsub/push")
def pubsub_push():
    """Handle Pub/Sub push messages."""
    envelope = request.get_json(silent=True)
    if not envelope or "message" not in envelope:
        print("[consumer] no Pub/Sub message received")
        return "No message received", 400

    # Extract message data
    pubsub_message = envelope["message"]
    message_id = pubsub_message.get("messageId")
    data_b64 = pubsub_message.get("data")

    if not data_b64:
        print("[consumer] no message data received")
        return "No message data", 400

    try:
        # Decode base64 to get raw AVRO bytes
        avro_bytes = base64.b64decode(data_b64)

        # Debug: Print first few bytes to verify it's AVRO
        print(f"[consumer] received {len(avro_bytes)} bytes: {avro_bytes[:10].hex()}")
        
        # Decode AVRO using schema
        decoded = fastavro.schemaless_reader(
            io.BytesIO(avro_bytes),
            parsed_schema
        )
        
        print(f"[consumer] processing message {message_id}")
        
        # Store as JSON (use dumps to ensure proper serialization)
        store_json(message_id, decoded)
        print(f"[consumer] stored JSON: {message_id}.json")
        
        # Store as Parquet
        parquet_path = store_parquet(decoded)
        print(f"[consumer] stored Parquet: {parquet_path}")
        
        # Load to BigQuery
        #load_to_bigquery(parquet_path)
        print(f"[consumer] loaded to BigQuery: {message_id}")
        
        # Return success to acknowledge the message
        return "", 204
        
    except Exception as e:
        error_msg = f"[consumer] error processing message {message_id}: {str(e)}"
        print(error_msg)
        # Return error to nack the message
        return error_msg, 400


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)