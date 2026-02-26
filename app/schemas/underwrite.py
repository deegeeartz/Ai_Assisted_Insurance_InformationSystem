from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import datetime


class CoverageBlock(BaseModel):
    id: str
    name: str
    description: str
    base_price: float
    icon: str  # Lucide icon name
    enabled: bool = True
    insurer_name: str = "Heirs Life Assurance"  # Which insurer offers this product
    category: str = "life"  # Product category: life, auto, gadget, home


class CalculatorRequest(BaseModel):
    age: int
    gender: str = "male"
    occupation: str = "employed"
    selected_coverage: List[str] = []  # IDs of selected blocks


class UnderwriteRequest(BaseModel):
    # Applicant Info
    holder_name: Optional[str] = None
    holder_email: Optional[str] = None
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


class ChatRequest(BaseModel):
    message: str
    role: Literal["consumer", "agent", "partner"] = "consumer"
    history: List[dict] = []  # [{"role": "user/model", "content": "..."}]
