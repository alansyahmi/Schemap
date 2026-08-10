from datetime import datetime, timezone
from typing import Generator
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from .config import settings

Base = declarative_base()

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    stripe_customer_id = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    licenses = relationship("License", back_populates="customer", cascade="all, delete-orphan")

class License(Base):
    __tablename__ = "licenses"

    id = Column(Integer, primary_key=True, index=True)
    key_hash = Column(String(64), unique=True, index=True, nullable=False)
    key_prefix = Column(String(16), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    stripe_customer_id = Column(String(255), nullable=False)
    stripe_subscription_id = Column(String(255), unique=True, nullable=True, index=True)
    stripe_checkout_session_id = Column(String(255), unique=True, nullable=False, index=True)
    stripe_price_id = Column(String(255), nullable=True)
    stripe_payment_intent_id = Column(String(255), nullable=True)
    plan_tier = Column(String(32), default="pro", nullable=False)
    billing_mode = Column(String(32), nullable=False)  # monthly, quarterly, semiannual, annual, lifetime
    status = Column(String(32), default="active", nullable=False)  # active, past_due, canceled, expired, revoked
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_verified_at = Column(DateTime(timezone=True), nullable=True)
    last_instance_name = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    customer = relationship("Customer", back_populates="licenses")

class StripeEvent(Base):
    __tablename__ = "stripe_events"

    event_id = Column(String(255), primary_key=True)
    event_type = Column(String(128), nullable=False)
    status = Column(String(32), default="processing", nullable=False)  # processing, completed, failed
    attempts = Column(Integer, default=0, nullable=False)
    last_error = Column(Text, nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

# Database Engine setup
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Creates all database tables."""
    Base.metadata.create_all(bind=engine)

def get_db() -> Generator:
    """Dependency provider for DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
