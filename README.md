# Intelligent Trade Surveillance & Market Abuse Detection

Enterprise-grade, GitHub-first implementation of a hybrid surveillance stack for equities, derivatives, crypto, and FX.

## Implemented Capability Coverage
- Rules engine: spoofing, layering/quote stuffing, wash trade + cycle rings, marking-the-close, pump-and-dump, pre-announcement trading, cross-asset spoofing, options-equity pinning.
- ML detection:
  - Unsupervised: Isolation Forest, DBSCAN, One-Class SVM.
  - Supervised pipeline: SVM + SMOTE training with evaluation and model registry.
  - Optional templates: XGBoost, TCN, GNN.
- Entity relationship graph: Neo4j + networkx fallback.
- Alerting and triage: severity scoring, deduplication, queue prioritization.
- Investigation workflows: case management, evidence aggregation, prior-alert linkage.
- Reporting: SAR markdown export + MAR XML export.
- Audit: hash-chained immutable activity log verification endpoint.
- Streaming/deployment: Kafka worker + production-oriented PyFlink job template + Kubernetes manifests + CI/CD + scheduled retraining/drift workflows.

## API Endpoints
- `POST /events`
- `GET /alerts`
- `GET /alerts/{alert_id}/priority`
- `POST /cases`
- `GET /cases`
- `GET /cases/{case_id}/evidence`
- `GET /reports/sar/{case_id}`
- `GET /reports/mar/{case_id}`
- `GET /audit/verify`
- `POST /graphql` (optional, enabled when `strawberry-graphql` is installed)
- `GET /health`
- `GET /metrics`
- `WS /ws/alerts`

## Quick Start

1. Configure environment:
```bash
cp .env.example .env
```

2. Start stack:
```bash
docker compose up --build
```

Frontend dashboard runs at `http://localhost:5173`.

3. Verify:
```bash
curl http://localhost:8000/health
```

4. Run tests:
```bash
python3 -m pytest
```

## Core Operations

```bash
make test
make lint
make backtest
make drift
make retrain
```

## Deployment
- Kubernetes manifests: `k8s/base/`
- GitHub workflows:
  - `.github/workflows/ci.yml`
  - `.github/workflows/docker-publish.yml`
  - `.github/workflows/retrain.yml`
  - `.github/workflows/drift-monitor.yml`
  - `.github/workflows/load-test.yml`

## Free-Tier Friendly Infrastructure
- Aiven PostgreSQL free
- Aiven Valkey free
- Aiven Kafka free
- Neo4j Aura Free

Runtime is designed to be stateless with remote backing services only.

## Status
Detailed phase-by-phase completion is tracked in `docs/CHECKLIST_STATUS.md`.
