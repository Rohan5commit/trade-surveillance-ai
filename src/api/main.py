from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timezone
import uuid

import numpy as np
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from loguru import logger
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import PlainTextResponse

from src.alerting.service import AlertService
from src.api.graphql_schema import build_graphql_router
from src.common.schemas import Alert, CaseCreateRequest, CaseResponse, IngestResponse, MarketEvent
from src.config.settings import settings
from src.detection.hybrid.scorer import combine_scores
from src.detection.ml.features import extract_session_features
from src.detection.ml.models import UnsupervisedEnsemble
from src.detection.rules.engine import RuleEngine
from src.investigation.evidence import collect_related_trades, link_prior_alerts, summarize_evidence
from src.investigation.queue import prioritize_alert
from src.investigation.case_manager import CaseManager
from src.preprocessing.normalizer import normalize_event
from src.reporting.audit import AuditTrail
from src.reporting.mar import MarPayload, render_mar_xml
from src.reporting.sar import SarPayload, render_sar_markdown

app = FastAPI(title="Intelligent Trade Surveillance API", version="0.1.0")

EVENTS_INGESTED = Counter("events_ingested_total", "Total events ingested")
ALERTS_GENERATED = Counter("alerts_generated_total", "Total alerts generated")
INGEST_LATENCY = Histogram("ingest_latency_seconds", "Latency for ingest endpoint")

rule_engine = RuleEngine()
alert_service = AlertService()
ml_ensemble = UnsupervisedEnsemble(contamination=0.01)
case_manager = CaseManager(settings.postgres_url or "sqlite+pysqlite:///:memory:")
case_manager.init_schema()
audit_trail = AuditTrail()

recent_events_by_account: dict[str, deque[MarketEvent]] = defaultdict(lambda: deque(maxlen=500))
all_events: deque[MarketEvent] = deque(maxlen=200_000)


class ConnectionManager:
    def __init__(self) -> None:
        self.connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.connections.discard(websocket)

    async def broadcast_alerts(self, alerts: list[Alert]) -> None:
        if not self.connections or not alerts:
            return
        payload = [a.model_dump(mode="json") for a in alerts]
        stale: list[WebSocket] = []
        for ws in self.connections:
            try:
                await ws.send_json({"type": "alerts", "data": payload})
            except Exception:
                stale.append(ws)
        for ws in stale:
            self.disconnect(ws)


ws_manager = ConnectionManager()
graphql_router = build_graphql_router(alert_service, case_manager)
if graphql_router is not None:
    app.include_router(graphql_router, prefix="/graphql")


@app.on_event("startup")
async def startup() -> None:
    logger.info("API starting in {env} mode", env=settings.environment)


@app.get("/health")
def health() -> JSONResponse:
    return JSONResponse({"status": "ok", "time": datetime.now(timezone.utc).isoformat()})


@app.get("/metrics")
def metrics() -> PlainTextResponse:
    return PlainTextResponse(generate_latest().decode("utf-8"), media_type="text/plain")


@app.post("/events", response_model=IngestResponse)
async def ingest_event(event: MarketEvent) -> IngestResponse:
    with INGEST_LATENCY.time():
        normalized = normalize_event(event)
        EVENTS_INGESTED.inc()
        all_events.append(normalized)

        recent_events_by_account[normalized.account_id].append(normalized)

        rule_alerts = rule_engine.process(normalized)

        ml_alerts: list[Alert] = []
        recent = list(recent_events_by_account[normalized.account_id])
        if len(recent) >= 25:
            try:
                features = extract_session_features(recent).vector.reshape(1, -1)
                if not ml_ensemble.fitted:
                    # Bootstrap with a rolling baseline from current account.
                    baseline = np.repeat(features, 30, axis=0)
                    baseline += np.random.normal(0, 0.01, baseline.shape)
                    ml_ensemble.fit(baseline)

                ml_score = float(ml_ensemble.score(features)[0])
                hybrid = combine_scores(
                    rule_based_score=max((a.score for a in rule_alerts), default=0.0),
                    ml_anomaly_score=ml_score,
                    historical_account_risk=0.4,
                )
                if hybrid.final_score >= 0.7:
                    ml_alerts.append(
                        Alert(
                            alert_id=str(uuid.uuid4()),
                            ts=normalized.ts,
                            detector="hybrid",
                            pattern="anomalous_behavior",
                            account_id=normalized.account_id,
                            symbol=normalized.symbol,
                            severity=hybrid.severity,
                            score=hybrid.final_score,
                            reason="Hybrid rule+ML score exceeded threshold.",
                            evidence={"ml_score": round(ml_score, 4)},
                        )
                    )
            except Exception as exc:
                logger.warning("ML scoring failed: {}", exc)

        accepted = alert_service.ingest(rule_alerts + ml_alerts)
        if accepted:
            ALERTS_GENERATED.inc(len(accepted))
            await ws_manager.broadcast_alerts(accepted)
            for alert in accepted:
                audit_trail.append(
                    actor="surveillance-engine",
                    action="alert_generated",
                    payload={"alert_id": alert.alert_id, "pattern": alert.pattern, "score": alert.score},
                )

        return IngestResponse(
            accepted=True,
            generated_alerts=len(accepted),
            alert_ids=[a.alert_id for a in accepted],
        )


@app.get("/alerts", response_model=list[Alert])
def list_alerts(limit: int = 100) -> list[Alert]:
    return alert_service.list_alerts(limit=limit)


@app.websocket("/ws/alerts")
async def alerts_websocket(websocket: WebSocket) -> None:
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


def _case_response(case_obj) -> CaseResponse:
    return CaseResponse(
        id=case_obj.id,
        alert_id=case_obj.alert_id,
        account_id=case_obj.account_id,
        symbol=case_obj.symbol,
        status=case_obj.status,
        severity=case_obj.severity,
        summary=case_obj.summary,
        created_at=case_obj.created_at,
    )


@app.post("/cases", response_model=CaseResponse)
def create_case(payload: CaseCreateRequest) -> CaseResponse:
    case = case_manager.create_case(
        alert_id=payload.alert_id,
        account_id=payload.account_id,
        symbol=payload.symbol,
        severity=payload.severity,
        summary=payload.summary,
    )
    audit_trail.append(
        actor="investigator-api",
        action="case_created",
        payload={"case_id": case.id, "alert_id": case.alert_id, "severity": case.severity},
    )
    return _case_response(case)


@app.get("/cases", response_model=list[CaseResponse])
def list_cases(limit: int = 100) -> list[CaseResponse]:
    return [_case_response(c) for c in case_manager.list_cases(limit=limit)]


@app.get("/reports/sar/{case_id}")
def generate_sar(case_id: int) -> PlainTextResponse:
    cases = {c.id: c for c in case_manager.list_cases(limit=1000)}
    case = cases.get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="case not found")

    report = render_sar_markdown(
        SarPayload(
            case_id=case.id,
            subject=case.account_id,
            activity_type=f"suspected_{case.severity}_market_abuse",
            amount_usd=0.0,
            start_date=case.created_at,
            end_date=case.created_at,
            narrative=case.summary,
        )
    )
    return PlainTextResponse(report, media_type="text/markdown")


@app.get("/reports/mar/{case_id}")
def generate_mar(case_id: int) -> PlainTextResponse:
    cases = {c.id: c for c in case_manager.list_cases(limit=1000)}
    case = cases.get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="case not found")

    xml = render_mar_xml(
        MarPayload(
            case_id=case.id,
            issuer=case.symbol,
            instrument=case.symbol,
            suspect=case.account_id,
            narrative=case.summary,
            detected_at=case.created_at,
        )
    )
    return PlainTextResponse(xml, media_type="application/xml")


@app.get("/cases/{case_id}/evidence")
def case_evidence(case_id: int) -> JSONResponse:
    cases = {c.id: c for c in case_manager.list_cases(limit=1000)}
    case = cases.get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="case not found")

    pivot_ts = case.created_at
    events = collect_related_trades(list(all_events), case.account_id, case.symbol, pivot_ts, days=3)
    prior = link_prior_alerts(alert_service.list_alerts(limit=5000), case.account_id, case.symbol)
    summary = summarize_evidence(
        Alert(
            alert_id=case.alert_id,
            ts=case.created_at,
            detector="case",
            pattern="case",
            account_id=case.account_id,
            symbol=case.symbol,
            severity=case.severity,
            score=0.5,
            reason=case.summary,
            evidence={},
        ),
        events,
        prior,
    )
    return JSONResponse({"case_id": case_id, "summary": summary, "sample_events": [e.model_dump(mode="json") for e in events[:10]]})


@app.get("/alerts/{alert_id}/priority")
def alert_priority(alert_id: str) -> JSONResponse:
    alerts = {a.alert_id: a for a in alert_service.list_alerts(limit=5000)}
    alert = alerts.get(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="alert not found")

    priority = prioritize_alert(alert, regulatory_deadline_days=30, account_risk_tier=3, age_minutes=10)
    return JSONResponse({"alert_id": alert_id, "priority_score": priority.score})


@app.get("/audit/verify")
def audit_verify() -> JSONResponse:
    return JSONResponse({"valid": audit_trail.verify_chain(), "records": len(audit_trail.records)})
