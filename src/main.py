from __future__ import annotations

import uvicorn

from src.api.main import app
from src.config.settings import settings


def run() -> None:
    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.environment == "development",
    )


if __name__ == "__main__":
    run()


__all__ = ["app", "run"]
