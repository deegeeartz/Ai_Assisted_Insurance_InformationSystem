from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base
import enum


class UserRole(str, enum.Enum):
    INSURER = "insurer"
    PARTNER = "partner"
    CONSUMER = "consumer"
    ADMIN = "admin"
    COMPLIANCE_OFFICER = "compliance_officer"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    company_name = Column(String, nullable=True)  # For insurers/partners
    role = Column(String, default=UserRole.CONSUMER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Tenant isolation
    tenant_id = Column(String, index=True, nullable=True)  # Links partners to their insurer

    # API Key for headless integrations (partners/banks)
    api_key = Column(String, unique=True, nullable=True, index=True)


class Policy(Base):
    __tablename__ = "policies"

    id = Column(Integer, primary_key=True, index=True)
    policy_number = Column(String, unique=True, index=True)
    product_type = Column(String)
    status = Column(String, default="active")  # active, lapsed, cancelled, claimed

    # Policyholder
    holder_name = Column(String)
    holder_email = Column(String)
    holder_age = Column(Integer)

    # Coverage details (JSON string)
    coverage_blocks = Column(String)  # Serialized list of selected blocks
    premium_monthly = Column(Float)
    premium_annual = Column(Float)

    # Relationships
    tenant_id = Column(String, index=True)  # Which insurer owns this product
    partner_id = Column(Integer, nullable=True)  # Which partner sold it (if any)
    manual_id = Column(Integer, ForeignKey("underwriting_manuals.id"))

    # Timestamps
    bound_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey("policies.id"))
    amount = Column(Float)
    currency = Column(String, default="NGN")

    # Split tracking
    insurer_share = Column(Float)
    partner_commission = Column(Float, default=0.0)
    platform_fee = Column(Float, default=0.0)

    # Payment gateway
    gateway = Column(String, default="paystack")  # paystack, stripe
    gateway_reference = Column(String, nullable=True)
    status = Column(String, default="pending")  # pending, success, failed

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SLARecord(Base):
    __tablename__ = "sla_records"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True)
    product_type = Column(String)

    # SLA Metrics
    metric_name = Column(String)  # e.g., "claims_processing_time"
    promised_value = Column(String)  # e.g., "24 hours"
    actual_value = Column(String, nullable=True)
    is_breached = Column(Boolean, default=False)

    measured_at = Column(DateTime(timezone=True), server_default=func.now())


class WebhookConfig(Base):
    __tablename__ = "webhook_configs"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True)
    event_type = Column(String)  # e.g., "policy.bound", "payment.success"
    url = Column(String)
    secret = Column(String, nullable=True)  # For HMAC signing
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class PlatformConfig(Base):
    __tablename__ = "platform_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    value = Column(String)
    description = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
