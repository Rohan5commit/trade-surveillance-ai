from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    alert_id: Mapped[str] = mapped_column(String(64), index=True)
    account_id: Mapped[str] = mapped_column(String(64), index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(32), default="triage")
    severity: Mapped[str] = mapped_column(String(16))
    summary: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class CaseManager:
    def __init__(self, db_url: str) -> None:
        if db_url.startswith("sqlite"):
            engine_kwargs = {"future": True, "connect_args": {"check_same_thread": False}}
            if ":memory:" in db_url:
                engine_kwargs["poolclass"] = StaticPool
            self.engine = create_engine(db_url, **engine_kwargs)
        else:
            self.engine = create_engine(db_url, future=True)
        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False, class_=Session)

    def init_schema(self) -> None:
        Base.metadata.create_all(self.engine)

    def create_case(self, tenant_id: str, alert_id: str, account_id: str, symbol: str, severity: str, summary: str) -> Case:
        with self.SessionLocal() as session:
            case = Case(
                tenant_id=tenant_id,
                alert_id=alert_id,
                account_id=account_id,
                symbol=symbol,
                severity=severity,
                summary=summary,
            )
            session.add(case)
            session.commit()
            session.refresh(case)
            return case

    def list_cases(self, tenant_id: str, limit: int = 100) -> Sequence[Case]:
        with self.SessionLocal() as session:
            return (
                session.query(Case)
                .filter(Case.tenant_id == tenant_id)
                .order_by(Case.created_at.desc())
                .limit(limit)
                .all()
            )

    def get_case(self, tenant_id: str, case_id: int) -> Case | None:
        with self.SessionLocal() as session:
            return session.query(Case).filter(Case.tenant_id == tenant_id, Case.id == case_id).first()
