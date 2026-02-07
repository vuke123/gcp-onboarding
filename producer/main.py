import json
import os
import requests
from google.cloud import pubsub_v1

STACKEX_API_URL = "https://api.stackexchange.com/2.3/questions"

PROJECT_ID = os.environ["PROJECT_ID"]
TOPIC_ID = os.environ["PUBSUB_TOPIC"]

STACKEX_SITE = os.getenv("STACKEX_SITE", "stackoverflow")
STACKEX_PAGESIZE = int(os.getenv("STACKEX_PAGESIZE", "10"))
STACKEX_SORT = os.getenv("STACKEX_SORT", "votes")
STACKEX_ORDER = os.getenv("STACKEX_ORDER", "desc")
STACKEX_TAGGED = os.getenv("STACKEX_TAGGED", "data-engineering")
STACKEX_KEY = os.getenv("STACK_EXCHANGE_API_KEY")
if not STACKEX_KEY:
    raise ValueError("STACK_EXCHANGE_API_KEY environment variable is required")

def fetch_questions() -> list[dict]:
    params = {
        "site": STACKEX_SITE,
        "pagesize": str(STACKEX_PAGESIZE),
        "order": STACKEX_ORDER,
        "sort": STACKEX_SORT,
        "tagged": STACKEX_TAGGED,
    }
    params["key"] = STACKEX_KEY

    r = requests.get(STACKEX_API_URL, params=params, timeout=30)
    r.raise_for_status()
    return r.json().get("items", [])

def main() -> None:
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

    items = fetch_questions()[:10]

    for i, item in enumerate(items, start=1):
        data = json.dumps(item).encode("utf-8")
        msg_id = publisher.publish(topic_path, data).result()
        print(f"[producer] published {i}/{len(items)} msg_id={msg_id}")

    print("[producer] done. exiting (Cloud Run Job should finish).")

if __name__ == "__main__":
    main()
