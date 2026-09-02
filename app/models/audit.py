from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.base import Base


class AuditLog(Base):
    """Immutable audit trail for all state-changing backend actions."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user_email = Column(String, nullable=True, index=True)
    action = Column(String, index=True)           # e.g. "login", "upload_manual", "pay", "suspend_tenant"
    resource_type = Column(String, nullable=True)  # e.g. "policy", "manual", "config", "user"
    resource_id = Column(String, nullable=True)    # e.g. policy_number, manual_id, config_key
    details = Column(Text, nullable=True)          # JSON string with extra context
    ip_address = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())


class UnderwritingDecisionLog(Base):
    """Records every underwriting decision — approved, declined, and referred."""
    __tablename__ = "underwriting_decisions"

    id = Column(Integer, primary_key=True, index=True)
    product_type = Column(String, index=True)
    tenant_id = Column(String, nullable=True, index=True)
    applicant_age = Column(Integer)
    applicant_name = Column(String, nullable=True)
    applicant_email = Column(String, nullable=True)
    status = Column(String, index=True)            # "approved", "declined", "referred"
    reason = Column(Text, nullable=True)
    premium_monthly = Column(String, nullable=True)
    premium_annual = Column(String, nullable=True)
    policy_number = Column(String, nullable=True)  # Only set if approved
    channel = Column(String, nullable=True)        # "d2c", "soap", "chat", "batch"
    partner_id = Column(Integer, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
