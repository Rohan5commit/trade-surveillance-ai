from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json


@dataclass
class AuditRecord:
    ts: datetime
    actor: str
    action: str
    payload: dict
    hash: str
    prev_hash: str


class AuditTrail:
    """Append-only hash-chained audit log for regulator traceability."""

    def __init__(self) -> None:
        self.records: list[AuditRecord] = []

    def append(self, actor: str, action: str, payload: dict) -> AuditRecord:
        prev_hash = self.records[-1].hash if self.records else "GENESIS"
        ts = datetime.now(timezone.utc)
        blob = json.dumps(
            {
                "ts": ts.isoformat(),
                "actor": actor,
                "action": action,
                "payload": payload,
                "prev_hash": prev_hash,
            },
            sort_keys=True,
        ).encode("utf-8")
        digest = hashlib.sha256(blob).hexdigest()
        record = AuditRecord(ts=ts, actor=actor, action=action, payload=payload, hash=digest, prev_hash=prev_hash)
        self.records.append(record)
        return record

    def verify_chain(self) -> bool:
        prev = "GENESIS"
        for record in self.records:
            blob = json.dumps(
                {
                    "ts": record.ts.isoformat(),
                    "actor": record.actor,
                    "action": record.action,
                    "payload": record.payload,
                    "prev_hash": prev,
                },
                sort_keys=True,
            ).encode("utf-8")
            if hashlib.sha256(blob).hexdigest() != record.hash:
                return False
            prev = record.hash
        return True
