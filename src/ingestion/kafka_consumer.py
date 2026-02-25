from __future__ import annotations

import json
from kafka import KafkaConsumer


def make_consumer(topic: str, bootstrap_servers: str, group_id: str = "surveillance") -> KafkaConsumer:
    return KafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="latest",
        enable_auto_commit=True,
        group_id=group_id,
    )
