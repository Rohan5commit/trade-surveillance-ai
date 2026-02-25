from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets

import jwt
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(128), default="default")
    key_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    key_prefix: Mapped[str] = mapped_column(String(24), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


@dataclass
class AuthUser:
    user_id: int
    tenant_id: str
    email: str


@dataclass
class ApiKeyIdentity:
    key_id: int
    tenant_id: str
    user_id: int
    name: str
    key_prefix: str


class AuthManager:
    def __init__(self, db_url: str, jwt_secret: str) -> None:
        if db_url.startswith("sqlite"):
            engine_kwargs = {"future": True, "connect_args": {"check_same_thread": False}}
            if ":memory:" in db_url:
                engine_kwargs["poolclass"] = StaticPool
            self.engine = create_engine(db_url, **engine_kwargs)
        else:
            self.engine = create_engine(db_url, future=True)
        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False, class_=Session)
        self.jwt_secret = jwt_secret or "dev-insecure-secret"

    def init_schema(self) -> None:
        Base.metadata.create_all(self.engine)

    def register_user(self, email: str, password: str) -> AuthUser:
        tenant_id = f"tenant_{secrets.token_hex(8)}"
        pwd_hash = self._hash_password(password)
        with self.SessionLocal() as session:
            user = User(email=email.lower().strip(), password_hash=pwd_hash, tenant_id=tenant_id)
            session.add(user)
            try:
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                raise ValueError("email already registered") from exc
            session.refresh(user)
            return AuthUser(user_id=user.id, tenant_id=user.tenant_id, email=user.email)

    def authenticate(self, email: str, password: str) -> AuthUser | None:
        with self.SessionLocal() as session:
            user = session.query(User).filter(User.email == email.lower().strip()).first()
            if not user:
                return None
            if not self._verify_password(password, user.password_hash):
                return None
            return AuthUser(user_id=user.id, tenant_id=user.tenant_id, email=user.email)

    def issue_token(self, user: AuthUser, expires_minutes: int = 60) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user.user_id),
            "email": user.email,
            "tenant_id": user.tenant_id,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
        }
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")

    def parse_token(self, token: str) -> AuthUser:
        payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
        return AuthUser(
            user_id=int(payload["sub"]),
            tenant_id=str(payload["tenant_id"]),
            email=str(payload["email"]),
        )

    def create_api_key(self, user: AuthUser, name: str = "default") -> tuple[ApiKeyIdentity, str]:
        raw = f"tsa_{secrets.token_urlsafe(36)}"
        key_hash = self._hash_api_key(raw)
        key_prefix = raw[:16]
        with self.SessionLocal() as session:
            key = ApiKey(
                tenant_id=user.tenant_id,
                user_id=user.user_id,
                name=name,
                key_hash=key_hash,
                key_prefix=key_prefix,
                is_active=True,
            )
            session.add(key)
            session.commit()
            session.refresh(key)
            identity = ApiKeyIdentity(
                key_id=key.id,
                tenant_id=key.tenant_id,
                user_id=key.user_id,
                name=key.name,
                key_prefix=key.key_prefix,
            )
            return identity, raw

    def list_api_keys(self, user: AuthUser) -> list[ApiKeyIdentity]:
        with self.SessionLocal() as session:
            rows = (
                session.query(ApiKey)
                .filter(ApiKey.user_id == user.user_id, ApiKey.is_active == True)  # noqa: E712
                .order_by(ApiKey.created_at.desc())
                .all()
            )
            return [
                ApiKeyIdentity(
                    key_id=row.id,
                    tenant_id=row.tenant_id,
                    user_id=row.user_id,
                    name=row.name,
                    key_prefix=row.key_prefix,
                )
                for row in rows
            ]

    def verify_api_key(self, raw_key: str) -> ApiKeyIdentity | None:
        key_hash = self._hash_api_key(raw_key)
        with self.SessionLocal() as session:
            row = session.query(ApiKey).filter(ApiKey.key_hash == key_hash, ApiKey.is_active == True).first()  # noqa: E712
            if not row:
                return None
            return ApiKeyIdentity(
                key_id=row.id,
                tenant_id=row.tenant_id,
                user_id=row.user_id,
                name=row.name,
                key_prefix=row.key_prefix,
            )

    def _hash_password(self, password: str) -> str:
        salt = secrets.token_hex(16)
        digest = hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()
        return f"{salt}${digest}"

    def _verify_password(self, password: str, stored: str) -> bool:
        try:
            salt, digest = stored.split("$", 1)
        except ValueError:
            return False
        actual = hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()
        return hmac.compare_digest(actual, digest)

    def _hash_api_key(self, key: str) -> str:
        return hashlib.sha256(key.encode("utf-8")).hexdigest()
