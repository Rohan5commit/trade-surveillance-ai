# Intelligent Trade Surveillance & Market Abuse Detection (Free/GitHub-First Scaffold)

This repository is a complete starter implementation for a hybrid surveillance platform covering:
- rules-based detection (spoofing, wash trading, quote stuffing, marking the close)
- unsupervised anomaly detection (Isolation Forest + DBSCAN + One-Class SVM)
- hybrid scoring and alert prioritization
- entity linkage graph scaffolding
- API + WebSocket alert stream
- CI/CD via GitHub Actions

## API Endpoints (implemented)
- `POST /events`: ingest normalized trade/order events
- `GET /alerts`: list deduplicated alerts
- `POST /cases`: open an investigation case
- `GET /cases`: list recent cases
- `GET /reports/sar/{case_id}`: generate SAR markdown draft
- `GET /health`: service liveness
- `GET /metrics`: Prometheus metrics
- `WS /ws/alerts`: real-time alert stream

## Why this is "free" and "no local storage" friendly
- Code and builds run from GitHub Actions.
- Runtime can be fully stateless when you provide remote services in `.env`.
- Local Docker stack is ephemeral (`tmpfs` for DB/graph in compose) for test/dev only.

## Project Structure

```text
trade-surveillance-ai/
├── src/
│   ├── ingestion/
│   ├── preprocessing/
│   ├── detection/
│   │   ├── rules/
│   │   ├── ml/
│   │   └── hybrid/
│   ├── entity_resolution/
│   ├── alerting/
│   ├── investigation/
│   ├── reporting/
│   └── api/
├── models/
├── config/
├── tests/
├── data/
├── dashboards/
├── docs/
└── scripts/
```

## Quick Start

1. Create environment file:
```bash
cp .env.example .env
```

2. Start services:
```bash
docker compose up --build
```

3. Health check:
```bash
curl http://localhost:8000/health
```

4. Ingest a sample event:
```bash
curl -X POST http://localhost:8000/events \
  -H 'Content-Type: application/json' \
  -d '{
    "event_id":"evt-1",
    "ts":"2026-02-25T12:00:00Z",
    "venue":"NASDAQ",
    "asset_class":"equity",
    "symbol":"AAPL.US",
    "account_id":"acct-1",
    "side":"BUY",
    "event_type":"new_order",
    "order_id":"ord-1",
    "quantity":100,
    "price":190.2,
    "order_type":"LIMIT",
    "metadata":{}
  }'
```

5. Run tests:
```bash
pytest
```

## GitHub-Only Build Flow

1. Create a new GitHub repository.
2. Push this project:
```bash
git remote add origin <your-repo-url>
git branch -M main
git add .
git commit -m "Initial trade surveillance scaffold"
git push -u origin main
```
3. CI will automatically run tests and build image.
4. Use the `Docker Publish` workflow to push image to GHCR for deployment.

Checklist implementation status is tracked in `docs/CHECKLIST_STATUS.md`.

## Minimal Free-Tier Production Setup

Use remote providers and set these env vars in your deploy target:
- `POSTGRES_URL` -> Neon
- `REDIS_URL` -> Upstash Redis
- `NEO4J_URI/USER/PASSWORD` -> Neo4j Aura Free
- `KAFKA_BOOTSTRAP_SERVERS` -> managed Kafka-compatible endpoint

## What is implemented now vs next

Implemented:
- real API, rule engine, unsupervised ML scoring path, metrics endpoint, test suite, CI workflows.

Next recommended additions:
- supervised models (SVM/XGBoost/TCN) training pipelines
- full Flink streaming job deployment
- communication surveillance ingestion (email/chat/voice)
- SAR/MAR filing adapters with regulator-specific schemas
