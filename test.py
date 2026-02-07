import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

STACKEX_API_URL = "https://api.stackexchange.com/2.3/questions"

# --- Config (no env vars required) ---
STACKEX_SITE = "stackoverflow"
STACKEX_PAGESIZE = 10
STACKEX_SORT = "votes"      # votes, activity, creation
STACKEX_ORDER = "desc"      # asc/desc
STACKEX_TAGGED = "data-engineering"  # tag filter
STACKEX_KEY: Optional[str] = None    # optional, leave None if you don't have it

TOPIC_FILE = Path("topic.jsonl")  # local "topic" storage (one JSON per line)


def fetch_questions() -> List[Dict[str, Any]]:
    """
    Fetch top questions from Stack Exchange API.
    Returns the raw 'items' list (no filtering) to mimic 'send all fields'.
    """
    params = {
        "site": STACKEX_SITE,
        "pagesize": str(STACKEX_PAGESIZE),
        "order": STACKEX_ORDER,
        "sort": STACKEX_SORT,
        "tagged": STACKEX_TAGGED,
    }
    if STACKEX_KEY:
        params["key"] = STACKEX_KEY

    r = requests.get(STACKEX_API_URL, params=params, timeout=30)
    r.raise_for_status()
    payload = r.json()
    return payload.get("items", [])


def producer_write_to_topic_file(items: List[Dict[str, Any]], topic_file: Path) -> None:
    """
    Simulates publishing messages to a topic by appending JSON lines to a file.
    Each line = one message (full JSON object).
    """
    # overwrite each run for clarity
    topic_file.write_text("", encoding="utf-8")

    with topic_file.open("a", encoding="utf-8") as f:
        for i, item in enumerate(items[:10], start=1):
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
            title = item.get("title", "<no title>")
            score = item.get("score", "?")
            link = item.get("link", "")
            print(f"[producer] {i}/10 wrote: score={score} title={title[:80]} link={link}")


def consumer_tail_topic_file(topic_file: Path, max_messages: int = 10) -> None:
    """
    Simulates a consumer that reads messages from the "topic" in real time.
    We read line-by-line and print the JSON.
    """
    print("\n[consumer] starting to read messages...\n")

    read_count = 0
    with topic_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            msg = json.loads(line)
            # "process" message: just print a few interesting fields + keep full JSON available
            print(
                json.dumps(
                    {
                        "question_id": msg.get("question_id"),
                        "title": msg.get("title"),
                        "score": msg.get("score"),
                        "tags": msg.get("tags"),
                        "link": msg.get("link"),
                    },
                    ensure_ascii=False,
                )
            )
            read_count += 1
            if read_count >= max_messages:
                break

    print(f"\n[consumer] done. read {read_count} messages.\n")


def main() -> None:
    print("[main] fetching Stack Exchange questions...")
    items = fetch_questions()

    if not items:
        print("[main] no items returned (try changing tag/site).")
        return

    print("[main] producing (writing) messages to local topic file...")
    producer_write_to_topic_file(items, TOPIC_FILE)

    # simulate a tiny delay like network / pubsub
    time.sleep(1)

    print("[main] consuming (reading) messages from local topic file...")
    consumer_tail_topic_file(TOPIC_FILE, max_messages=10)


if __name__ == "__main__":
    main()
