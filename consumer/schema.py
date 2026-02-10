"""AVRO schema definition for Stack Exchange posts."""

STACKEX_POST_SCHEMA = {
    "type": "record",
    "name": "StackExchangePost",
    "namespace": "com.syntio.stackexchange",
    "fields": [
        {"name": "question_id", "type": "long"},  # Stack Exchange post ID
        {"name": "title", "type": "string"},
        {"name": "link", "type": "string"},
        {"name": "score", "type": "int"},
        {"name": "creation_date", "type": "long"},  # Unix timestamp
        {"name": "answer_count", "type": "int"},
        {"name": "is_answered", "type": "boolean"},
        {"name": "view_count", "type": "int"},
        {"name": "tags", "type": {"type": "array", "items": "string"}},
        {"name": "owner", "type": {
            "type": "record",
            "name": "Owner",
            "fields": [
                {"name": "user_id", "type": ["null", "long"]},
                {"name": "display_name", "type": "string"},
                {"name": "reputation", "type": ["null", "int"]},
                {"name": "user_type", "type": "string"}
            ]
        }}
    ]
}
