from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import datetime


class CoverageBlock(BaseModel):
    name: str  # e.g., "Life", "Critical Illness", "Dental"
    enabled: bool = True


class UnderwriteRequest(BaseModel):
    # Applicant Info
    age: int
    gender: Optional[str] = None
    occupation: Optional[str] = None
    smoker: bool = False
    location: Optional[str] = None

    # Coverage Selection (Lego Blocks)
    coverage_selection: List[CoverageBlock] = []

    # Natural Language (for Chatbot / Intent Router)
    natural_language_query: Optional[str] = None

    # Role Context
    role: Literal["consumer", "agent"] = "consumer"

    # Product Routing (optional - if not provided, AI will infer)
    product_type: Optional[str] = None


class UnderwriteDecision(BaseModel):
    status: Literal["approved", "declined", "referred"]
    premium_monthly: Optional[float] = None
    premium_annual: Optional[float] = None
    coverage_details: dict = {}
    reason: str  # Explainability: "Why" this decision
    plain_english_summary: str  # Consumer-friendly explanation
    agent_notes: Optional[str] = None  # Only populated for role=agent
    policy_number: Optional[str] = None
    sla_commitments: dict = {}
    timestamp: datetime = datetime.now()


class SOAPEnvelope(BaseModel):
    """Wrapper for SOAP/XML responses"""
    header: dict = {}
    body: dict = {}
