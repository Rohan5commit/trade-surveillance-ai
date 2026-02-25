# Operations Runbook

## Startup
1. Copy `.env.example` to `.env` and fill remote service URLs.
2. Run `docker compose up --build`.
3. Verify health: `GET /health`.
4. Verify metrics: `GET /metrics`.

## Incident Response
1. Check API error rate in Grafana.
2. Check Kafka consumer lag.
3. Validate DB/Redis/Neo4j connectivity.
4. Fallback to rules-only mode if ML scoring fails.

## Model Maintenance
- Weekly: sample 100 alerts and label TP/FP.
- Monthly: retrain unsupervised baselines + supervised models.
- Quarterly: full validation and threshold calibration.
