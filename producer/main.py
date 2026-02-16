"""Producer service for Stack Exchange posts to Pub/Sub with AVRO encoding."""

import io
import json
import os
import time
from datetime import datetime

import fastavro
import requests
from google.cloud import pubsub_v1

from schema import STACKEX_POST_SCHEMA

# API Constants
STACKEX_API_URL = "https://api.stackexchange.com/2.3/questions"

# Load config from env
PROJECT_ID = os.environ["PROJECT_ID"]
TOPIC_ID = os.environ["PUBSUB_TOPIC"]
DLQ_TOPIC_ID = os.environ["DLQ_TOPIC_ID"]

# Stack Exchange API key (required)
STACKEX_KEY = os.getenv("STACK_EXCHANGE_API_KEY")
if not STACKEX_KEY:
    raise ValueError("STACK_EXCHANGE_API_KEY environment variable is required")

# Optional config with defaults
STACKEX_SITE = os.getenv("STACKEX_SITE", "stackoverflow")
STACKEX_PAGESIZE = int(os.getenv("STACKEX_PAGESIZE", "100"))
STACKEX_SORT = os.getenv("STACKEX_SORT", "votes")
STACKEX_ORDER = os.getenv("STACKEX_ORDER", "desc")
STACKEX_TAGGED = os.getenv("STACKEX_TAGGED", "data-engineering")

def fetch_top_posts() -> list[dict]:
    params = {
        "site": STACKEX_SITE,
        "pagesize": str(STACKEX_PAGESIZE),
        "order": STACKEX_ORDER,
        "sort": STACKEX_SORT,
        "tagged": STACKEX_TAGGED,
        "key": STACKEX_KEY
    }

    r = requests.get(STACKEX_API_URL, params=params, timeout=30)
    r.raise_for_status()
    return r.json().get("items", [])


def transform_post(post: dict) -> dict:
    # Extract owner data safely
    owner = post.get("owner", {})
    
    return {
        "question_id": post.get("question_id", 0),  # Required
        "title": post.get("title"),  # Nullable
        "link": post.get("link"),  # Nullable
        "score": post.get("score"),  # Nullable
        "answer_count": post.get("answer_count"),  # Nullable
        "view_count": post.get("view_count"),  # Nullable
        "is_answered": post.get("is_answered"),  # Nullable
        "creation_date": post.get("creation_date"),  # Nullable
        "last_activity_date": post.get("last_activity_date"),  # Nullable
        "tags": post.get("tags"),  # Nullable array
        "content_license": post.get("content_license"),  # Nullable
        "owner": {
            "account_id": owner.get("account_id"),  # Nullable
            "user_id": owner.get("user_id"),  # Nullable
            "reputation": owner.get("reputation"),  # Nullable
            "user_type": owner.get("user_type"),  # Nullable
            "display_name": owner.get("display_name"),  # Nullable
            "profile_image": owner.get("profile_image"),  # Nullable
            "link": owner.get("link")  # Nullable
        } if owner else None  # Entire owner record is nullable
    }


def encode_avro(post: dict) -> bytes:
    parsed_schema = fastavro.parse_schema(STACKEX_POST_SCHEMA)
    output = io.BytesIO()
    fastavro.schemaless_writer(output, parsed_schema, post)
    return output.getvalue()

def publish_main(post: dict) -> None:
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
                del post["question_id"]  # Remove required field


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
