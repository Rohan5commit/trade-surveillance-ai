from __future__ import annotations

import json
from kafka import KafkaConsumer

from src.config.settings import settings


def make_consumer(topic: str, bootstrap_servers: str, group_id: str = "surveillance") -> KafkaConsumer:
    kwargs = {
        "bootstrap_servers": bootstrap_servers,
        "value_deserializer": lambda m: json.loads(m.decode("utf-8")),
        "auto_offset_reset": "latest",
        "enable_auto_commit": True,
        "group_id": group_id,
    }
    if settings.kafka_security_protocol:
        kwargs["security_protocol"] = settings.kafka_security_protocol
    if settings.kafka_ssl_cafile:
        kwargs["ssl_cafile"] = settings.kafka_ssl_cafile
    if settings.kafka_ssl_certfile:
        kwargs["ssl_certfile"] = settings.kafka_ssl_certfile
    if settings.kafka_ssl_keyfile:
        kwargs["ssl_keyfile"] = settings.kafka_ssl_keyfile
    return KafkaConsumer(topic, **kwargs)
