# Architecture Overview

## Core Components
- Ingestion: Kafka/FIX/WebSocket connector layer.
- Preprocessing: normalization to canonical event schema.
- Detection:
  - Rules engine for deterministic signatures.
  - Unsupervised ML ensemble (Isolation Forest + One-Class SVM + DBSCAN).
  - Hybrid scorer for prioritization.
- Entity resolution graph for account/account-owner linkage.
- Alert management and case lifecycle.
- API + WebSocket for investigation tools.

## Stateless Runtime Principle
Production runtime is designed to be stateless:
- Use remote PostgreSQL for cases and audit logs.
- Use remote Redis for dedup/session state.
- Use remote Neo4j for relationship graph.
- Use managed Kafka-compatible broker for streams.
- Do not depend on local container volumes for persistence.

## Recommended Free-Tier Backing Services
- PostgreSQL: Neon free plan.
- Redis: Upstash free plan.
- Neo4j: Neo4j Aura Free.
- Kafka-compatible stream: Upstash Kafka or Redpanda Cloud trial.
- Deployment: GitHub Actions + Cloud Run/Fly.io/Render free tier (availability varies).
