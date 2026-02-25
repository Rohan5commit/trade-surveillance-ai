# API Keys / Secrets Needed

Leave these blank initially; fill before production use:

- `POSTGRES_URL` (remote PostgreSQL)
- `REDIS_URL` (remote Redis)
- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`
- `KAFKA_BOOTSTRAP_SERVERS` (managed Kafka-compatible broker)
- `KAFKA_SECURITY_PROTOCOL` (`SSL` for Aiven cert auth)
- `KAFKA_SSL_KEYFILE` (path to private key)
- `KAFKA_SSL_CERTFILE` (path to client cert)
- `KAFKA_SSL_CAFILE` (path to CA cert)
- `POLYGON_API_KEY` (optional market data)
- `FINNHUB_API_KEY` (optional market data)
- `JWT_SECRET` (if auth enabled)
- `SENTRY_DSN` (optional observability)
- `MLFLOW_TRACKING_URI` (optional remote model registry/tracking)
