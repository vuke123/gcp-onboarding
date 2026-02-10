"""Producer service that fetches Stack Exchange posts and publishes them to Pub/Sub using AVRO encoding."""

import io
import json
import os
import time
from datetime import datetime

import fastavro
import requests
from google.cloud import pubsub_v1
from google.cloud import secretmanager

from schema import STACKEX_POST_SCHEMA

# API Constants
STACKEX_API_URL = "https://api.stackexchange.com/2.3/questions"

# Load config from env
PROJECT_ID = os.environ["PROJECT_ID"]
TOPIC_ID = os.environ["PUBSUB_TOPIC"]
DLQ_TOPIC_ID = os.environ["DLQ_TOPIC_ID"]

# Optional config with defaults
STACKEX_SITE = os.getenv("STACKEX_SITE", "stackoverflow")
STACKEX_PAGESIZE = int(os.getenv("STACKEX_PAGESIZE", "10"))
STACKEX_SORT = os.getenv("STACKEX_SORT", "votes")
STACKEX_ORDER = os.getenv("STACKEX_ORDER", "desc")
STACKEX_TAGGED = os.getenv("STACKEX_TAGGED", "data-engineering")

def get_secret(secret_id: str) -> str:
    """Retrieve a secret from Google Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")


def fetch_top_posts() -> list[dict]:
    """Fetch top Stack Exchange posts based on configuration."""
    params = {
        "site": STACKEX_SITE,
        "pagesize": str(STACKEX_PAGESIZE),
        "order": STACKEX_ORDER,
        "sort": STACKEX_SORT,
        "tagged": STACKEX_TAGGED,
        "key": get_secret("STACK_EXCHANGE_API_KEY")
    }

    r = requests.get(STACKEX_API_URL, params=params, timeout=30)
    r.raise_for_status()
    return r.json().get("items", [])


def transform_post(post: dict) -> dict:
    """Transform raw API response to match our AVRO schema."""
    return {
        "question_id": post["question_id"],
        "title": post["title"],
        "link": post["link"],
        "score": post["score"],
        "creation_date": post["creation_date"],
        "answer_count": post["answer_count"],
        "is_answered": post["is_answered"],
        "view_count": post["view_count"],
        "tags": post["tags"],
        "owner": {
            "user_id": post["owner"].get("user_id"),
            "display_name": post["owner"]["display_name"],
            "reputation": post["owner"].get("reputation"),
            "user_type": post["owner"]["user_type"]
        }
    }


def encode_avro(post: dict) -> bytes:
    """Encode a post dict into AVRO binary format."""
    parsed_schema = fastavro.parse_schema(STACKEX_POST_SCHEMA)
    output = io.BytesIO()
    fastavro.schemaless_writer(output, parsed_schema, post)
    return output.getvalue()

def publish_main(post: dict) -> None:
    """Publish a post to the main topic as AVRO."""
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

    try:
        # Transform and encode as AVRO
        transformed = transform_post(post)
        avro_bytes = encode_avro(transformed)

        # Publish with metadata
        future = publisher.publish(
            topic_path,
            data=avro_bytes,
            encoding="avro",
            schema_version="v1",
            source="stackexchange-producer"
        )
        msg_id = future.result()
        print(f"[producer] published to main topic: {msg_id}")

    except Exception as e:
        print(f"[producer] error publishing to main topic: {e}")
        publish_dlq(post, str(e), "publish")
        raise


def publish_dlq(post: dict, error_reason: str, failed_stage: str) -> None:
    """Publish a failed post to the dead-letter queue (DLQ)."""
    publisher = pubsub_v1.PublisherClient()
    dlq_path = publisher.topic_path(PROJECT_ID, DLQ_TOPIC_ID)

    # Publish original JSON with error details
    future = publisher.publish(
        dlq_path,
        data=json.dumps(post).encode("utf-8"),
        error_reason=error_reason,
        failed_stage=failed_stage,
        source="stackexchange-producer",
        timestamp=datetime.utcnow().isoformat()
    )
    msg_id = future.result()
    print(f"[producer] published to DLQ: {msg_id} (reason: {error_reason})")


def main() -> None:
    """Main function that orchestrates the producer workflow."""
    posts = fetch_top_posts()
    print(f"[producer] fetched {len(posts)} posts")

    # Process each post
    for i, post in enumerate(posts, 1):
        try:
            print(f"\n[producer] processing post {i}/{len(posts)}")

            # Negative test: deliberately break one message
            if i == len(posts):  # Last message
                print("[producer] simulating invalid message...")
                del post["title"]  # Remove required field

            publish_main(post)

        except Exception as e:
            print(f"[producer] error processing post {i}: {e}")
            # Error already logged and sent to DLQ in publish_main

        # Avoid timeout
        if i < len(posts):
            time.sleep(3)

    print("\n[producer] done. exiting (Cloud Run Job should finish).")

if __name__ == "__main__":
    main()
