from __future__ import annotations

import json
import os
import time

import requests
from kafka import KafkaConsumer

from src.config.settings import settings


def _consumer() -> KafkaConsumer:
    kwargs = {
        "bootstrap_servers": settings.kafka_bootstrap_servers,
        "value_deserializer": lambda m: json.loads(m.decode("utf-8")),
        "auto_offset_reset": "latest",
        "enable_auto_commit": True,
        "group_id": "surveillance-worker",
    }
    if settings.kafka_security_protocol:
        kwargs["security_protocol"] = settings.kafka_security_protocol
    if settings.kafka_ssl_cafile:
        kwargs["ssl_cafile"] = settings.kafka_ssl_cafile
    if settings.kafka_ssl_certfile:
        kwargs["ssl_certfile"] = settings.kafka_ssl_certfile
    if settings.kafka_ssl_keyfile:
        kwargs["ssl_keyfile"] = settings.kafka_ssl_keyfile
    return KafkaConsumer("order-stream", **kwargs)


def run_worker() -> None:
    api_url = os.getenv("SURVEILLANCE_API_URL", "http://api:8000")
    while True:
        try:
            consumer = _consumer()
            for message in consumer:
                payload = message.value
                requests.post(f"{api_url}/events", json=payload, timeout=5)
        except Exception as exc:
            print(f"worker_error={exc}")
            time.sleep(2)


if __name__ == "__main__":
    run_worker()
