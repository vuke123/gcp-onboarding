import base64
import json
import os
from flask import Flask, request

app = Flask(__name__)

@app.get("/")
def health():
    return "OK", 200

@app.post("/pubsub/push")
def pubsub_push():
    """
    Pub/Sub push sends JSON envelope like:
    {
      "message": {
        "data": "base64...",
        "attributes": {...},
        "messageId": "...",
        ...
      },
      "subscription": "projects/.../subscriptions/..."
    }
    If we return 200, Pub/Sub considers it ACKed.
    """
    envelope = request.get_json(silent=True)
    if not envelope or "message" not in envelope:
        return ("Bad Request: no Pub/Sub message received", 400)

    msg = envelope["message"]
    data_b64 = msg.get("data", "")
    attributes = msg.get("attributes", {})
    message_id = msg.get("messageId")

    try:
        decoded = base64.b64decode(data_b64).decode("utf-8") if data_b64 else ""
        payload = json.loads(decoded) if decoded else {}
    except Exception as e:
        print(f"[consumer] decode/parse error: {e}")
        return ("Bad Request: invalid message data", 400)

    print(json.dumps(
        {
            "messageId": message_id,
            "attributes": attributes,
            "payload": payload
        },
        ensure_ascii=False
    ))

    return ("", 200)

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
