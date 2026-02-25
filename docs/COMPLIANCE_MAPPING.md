# Compliance Mapping (Starter)

## US (SEC / FINRA)
- FINRA Rule 3110 supervision support via alerting + case workflow.
- Audit trail requirement addressed by immutable alert/case event records in PostgreSQL.
- Cross-market surveillance enabled by normalized multi-asset schema and relationship graph.

## EU (MiFID II / MAR)
- Quote-to-trade ratio monitor implemented in quote-stuffing rule.
- Case and alert retention policy configurable for 5+ years in remote DB lifecycle settings.
- MAR report export path provided in reporting module scaffold.

## Explainability
- Rule alerts include deterministic evidence fields.
- ML alerts include component scores and can be extended with SHAP/LIME in `requirements-optional.txt`.
