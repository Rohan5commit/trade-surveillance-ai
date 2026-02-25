from __future__ import annotations

from typing import Any


def build_graphql_router(alert_service: Any, case_manager: Any):
    """Optional GraphQL endpoint. Requires strawberry-graphql.

    Install with:
      pip install strawberry-graphql[fastapi]
    """
    try:
        import strawberry
        from strawberry.fastapi import GraphQLRouter
    except Exception:
        return None

    @strawberry.type
    class AlertType:
        alert_id: str
        pattern: str
        account_id: str
        symbol: str
        severity: str
        score: float

    @strawberry.type
    class CaseType:
        id: int
        alert_id: str
        account_id: str
        symbol: str
        severity: str
        summary: str

    @strawberry.type
    class Query:
        @strawberry.field
        def alerts(self, tenant_id: str, limit: int = 50) -> list[AlertType]:
            out = []
            for a in alert_service.list_alerts_for_tenant(tenant_id=tenant_id, limit=limit):
                out.append(
                    AlertType(
                        alert_id=a.alert_id,
                        pattern=a.pattern,
                        account_id=a.account_id,
                        symbol=a.symbol,
                        severity=a.severity,
                        score=a.score,
                    )
                )
            return out

        @strawberry.field
        def cases(self, tenant_id: str, limit: int = 50) -> list[CaseType]:
            out = []
            for c in case_manager.list_cases(tenant_id=tenant_id, limit=limit):
                out.append(
                    CaseType(
                        id=c.id,
                        alert_id=c.alert_id,
                        account_id=c.account_id,
                        symbol=c.symbol,
                        severity=c.severity,
                        summary=c.summary,
                    )
                )
            return out

    schema = strawberry.Schema(query=Query)
    return GraphQLRouter(schema)
