"""AVRO schema definition for Stack Exchange posts."""

STACKEX_POST_SCHEMA = {
    "type": "record",
    "name": "StackExQuestion",
    "namespace": "lab2.stackex",
    "fields": [
        {"name": "question_id", "type": "long"},
        {"name": "title", "type": ["null", "string"], "default": None},
        {"name": "link", "type": ["null", "string"], "default": None},
        {"name": "score", "type": ["null", "int"], "default": None},
        {"name": "answer_count", "type": ["null", "int"], "default": None},
        {"name": "view_count", "type": ["null", "int"], "default": None},
        {"name": "is_answered", "type": ["null", "boolean"], "default": None},
        {"name": "creation_date", "type": ["null", "long"], "default": None},
        {"name": "last_activity_date", "type": ["null", "long"], "default": None},
        {
            "name": "tags",
            "type": ["null", {"type": "array", "items": "string"}],
            "default": None
        },
        {"name": "content_license", "type": ["null", "string"], "default": None},
        {
            "name": "owner",
            "type": [
                "null",
                {
                    "type": "record",
                    "name": "Owner",
                    "fields": [
                        {"name": "account_id", "type": ["null", "long"], "default": None},
                        {"name": "user_id", "type": ["null", "long"], "default": None},
                        {"name": "reputation", "type": ["null", "int"], "default": None},
                        {"name": "user_type", "type": ["null", "string"], "default": None},
                        {"name": "display_name", "type": ["null", "string"], "default": None},
                        {"name": "profile_image", "type": ["null", "string"], "default": None},
                        {"name": "link", "type": ["null", "string"], "default": None}
                    ]
                }
            ],
            "default": None
        }
    ]
}
