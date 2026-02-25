from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path


@dataclass
class ModelVersion:
    name: str
    version: str
    metrics: dict[str, float]
    artifact_uri: str


class LocalModelRegistry:
    """Simple JSON registry fallback. Use MLflow in production."""

    def __init__(self, path: str = "models/registry.json") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def register(self, model: ModelVersion) -> None:
        current = json.loads(self.path.read_text(encoding="utf-8"))
        current.append(
            {
                "name": model.name,
                "version": model.version,
                "metrics": model.metrics,
                "artifact_uri": model.artifact_uri,
            }
        )
        self.path.write_text(json.dumps(current, indent=2), encoding="utf-8")

    def latest(self, name: str) -> ModelVersion | None:
        current = json.loads(self.path.read_text(encoding="utf-8"))
        candidates = [m for m in current if m.get("name") == name]
        if not candidates:
            return None
        m = candidates[-1]
        return ModelVersion(name=m["name"], version=m["version"], metrics=m["metrics"], artifact_uri=m["artifact_uri"])
