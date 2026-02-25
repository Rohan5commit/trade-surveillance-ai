# Implementation Checklist Status

Legend: `[x] implemented in this repo`, `[~] scaffolded/template`, `[ ] pending`

## Phase 1: Architecture & Infrastructure
- [x] Project structure and modular services
- [x] Technology stack baseline (FastAPI, Kafka-compatible stream, Postgres, Redis, Neo4j)
- [x] Docker + Compose local ephemeral environment
- [x] GitHub Actions CI + Docker publish workflow
- [~] Full production Kubernetes manifests (starter only)

## Phase 2: Ingestion & Preprocessing
- [x] Canonical event schema and normalization pipeline
- [x] Kafka consumer helper
- [~] Exchange-specific FIX/WebSocket adapters (to be implemented per venue)
- [x] Data quality checks embedded in rule/feature processing path

## Phase 3: Rules Engine
- [x] Spoofing
- [x] Wash trading (self-trade baseline)
- [x] Quote stuffing
- [x] Marking the close
- [x] Pump-and-dump (metadata-driven baseline)
- [x] Pre-announcement insider activity baseline
- [~] Cross-market options/equity manipulation enrichment

## Phase 4: ML Detection
- [x] Unsupervised ensemble: Isolation Forest + DBSCAN + One-Class SVM
- [x] Hybrid score combiner
- [x] Supervised model templates: SVM + XGBoost
- [x] Optional TCN and GNN model skeletons
- [ ] Full training datasets and model registry integration

## Phase 5: Alerting & Investigation
- [x] Alert creation, scoring, severity bands, dedup
- [x] Case manager schema/service scaffold (SQLAlchemy)
- [x] SAR markdown report template
- [~] Full investigator UI and workflow automation

## Phase 6: Real-Time Deployment & Monitoring
- [x] Metrics endpoint for Prometheus
- [x] Grafana/Prometheus stack in compose
- [x] Flink job skeleton
- [~] Production-grade Flink job with stateful CEP and exactly-once semantics

## Phase 7: Testing & Validation
- [x] Unit tests for rules and scoring
- [x] Integration test for API ingest
- [ ] Full historical replay + 1M events/sec load testing harness

## Phase 8: Compliance & Documentation
- [x] Architecture, compliance mapping, runbook docs
- [x] API key/secret inventory
- [~] Jurisdiction-specific regulator submission adapters (XML formats)

## Phase 9: Continuous Improvement
- [x] Retraining and feedback loops documented
- [ ] Automated drift detection job and scheduled retraining pipeline
