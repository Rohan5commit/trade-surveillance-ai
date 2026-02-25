from __future__ import annotations

import modal


app = modal.App("trade-surveillance-ai")
image = modal.Image.debian_slim().pip_install_from_requirements("requirements.txt")


@app.function(image=image, scaledown_window=60)
@modal.asgi_app()
def fastapi_app():
    import os

    os.environ["ENVIRONMENT"] = "demo"
    os.environ["DEMO_MODE"] = "true"
    os.environ["REQUIRE_API_KEY"] = "false"
    os.environ["JWT_SECRET"] = "demo-insecure-secret"

    from src.api.main import app as api_app

    return api_app
