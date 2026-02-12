from pydantic import BaseModel, EmailStr
from typing import Optional, Literal
from datetime import datetime


# --- Auth Schemas ---
class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    company_name: Optional[str] = None
    role: Literal["insurer", "partner", "consumer"] = "consumer"


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    company_name: Optional[str] = None
    role: str
    api_key: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class LoginRequest(BaseModel):
    email: str
    password: str


# --- Payment Schemas ---
class PaymentRequest(BaseModel):
    policy_number: str
    amount: float
    currency: str = "NGN"
    gateway: Literal["paystack", "stripe"] = "paystack"


class PaymentResponse(BaseModel):
    id: int
    policy_id: int
    amount: float
    insurer_share: float
    partner_commission: float
    platform_fee: float
    status: str
    gateway_reference: Optional[str] = None

    class Config:
        from_attributes = True


# --- SLA Schemas ---
class SLAResponse(BaseModel):
    metric_name: str
    promised_value: str
    actual_value: Optional[str] = None
    is_breached: bool
    measured_at: datetime

    class Config:
        from_attributes = True


# --- Webhook Schemas ---
class WebhookCreate(BaseModel):
    event_type: str
    url: str
    secret: Optional[str] = None


class WebhookResponse(BaseModel):
    id: int
    event_type: str
    url: str
    is_active: bool

    class Config:
        from_attributes = True
