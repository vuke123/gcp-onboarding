import json
import os
import requests
from collections.abc import Mapping, Sequence

STACKEX_API_URL = "https://api.stackexchange.com/2.3/questions"

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
        "key": STACKEX_KEY,
    }

    r = requests.get(STACKEX_API_URL, params=params, timeout=30)
    r.raise_for_status()
    return r.json().get("items", [])


def summarize_structure(obj, max_depth=4, depth=0):
    """
    Returns a lightweight "shape" of JSON-like data:
    - dict -> {key: <shape>}
    - list -> [<shape of first N unique item types>]
    - scalar -> type name
    """
    if depth >= max_depth:
        return "..."

    if isinstance(obj, Mapping):
        out = {}
        for k, v in obj.items():
            out[k] = summarize_structure(v, max_depth=max_depth, depth=depth + 1)
        return out

    if isinstance(obj, Sequence) and not isinstance(obj, (str, bytes, bytearray)):
        # Show up to 3 example shapes from the list
        shapes = []
        seen = set()
        for item in obj[:10]:
            s = json.dumps(summarize_structure(item, max_depth=max_depth, depth=depth + 1), sort_keys=True)
            if s not in seen:
                seen.add(s)
                shapes.append(json.loads(s))
            if len(shapes) >= 3:
                break
        return shapes if shapes else []

    return type(obj).__name__


def main() -> None:
    items = fetch_questions()[:10]

    print("\n=== SAMPLE RAW ITEM (first question) ===")
    if not items:
        print("No items returned.")
        return

    print(json.dumps(items[0], indent=2, ensure_ascii=False)[:4000])  # truncate to keep it readable

    print("\n=== TOP-LEVEL KEYS (first question) ===")
    print(sorted(items[0].keys()))

    print("\n=== STRUCTURE / SHAPE (first question) ===")
    shape = summarize_structure(items[0], max_depth=4)
    print(json.dumps(shape, indent=2, ensure_ascii=False)[:8000])

    print("\n=== QUICK TYPES (selected fields) ===")
    for field in ["question_id", "title", "link", "score", "tags", "creation_date", "owner"]:
        val = items[0].get(field)
        print(f"- {field}: {type(val).__name__}")

    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
