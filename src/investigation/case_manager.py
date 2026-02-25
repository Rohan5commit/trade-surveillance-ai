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
    alert_id: Mapped[str] = mapped_column(String(64), index=True)
    account_id: Mapped[str] = mapped_column(String(64), index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(32), default="triage")
    severity: Mapped[str] = mapped_column(String(16))
    summary: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class CaseManager:
    def __init__(self, db_url: str) -> None:
        if db_url.startswith("sqlite") and ":memory:" in db_url:
            self.engine = create_engine(
                db_url,
                future=True,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
            )
        else:
            self.engine = create_engine(db_url, future=True)
        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False, class_=Session)

    def init_schema(self) -> None:
        Base.metadata.create_all(self.engine)

    def create_case(self, alert_id: str, account_id: str, symbol: str, severity: str, summary: str) -> Case:
        with self.SessionLocal() as session:
            case = Case(
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

    def list_cases(self, limit: int = 100) -> Sequence[Case]:
        with self.SessionLocal() as session:
            return session.query(Case).order_by(Case.created_at.desc()).limit(limit).all()
