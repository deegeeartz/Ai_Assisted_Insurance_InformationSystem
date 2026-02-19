from fastapi import APIRouter, Depends, HTTPException, Request, Security, Query
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.schemas.underwrite import UnderwriteRequest, UnderwriteDecision, ChatRequest
from app.services.underwriting import route_to_product, execute_underwriting
from app.services.protocol_adapter import create_soap_response
from app.services.policy_number import generate_policy_number
from app.services.auth import get_user_by_api_key
from app.models.core import Policy, Payment, User
from app.models.chat_log import ChatLog
import json
import uuid
import time
from datetime import datetime

import logging

logger = logging.getLogger(__name__)


def normalize_content(content):
    """Normalize LLM response content.
    Newer langchain-google-genai returns list of dicts like:
    [{'type': 'text', 'text': '...actual text...', 'extras': {...}}]
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts = []
        for part in content:
            if isinstance(part, dict) and 'text' in part:
                texts.append(part['text'])
            elif isinstance(part, str):
                texts.append(part)
            else:
                texts.append(str(part))
        return " ".join(texts)
    return str(content)


router = APIRouter()

api_key_header = APIKeyHeader(name="X-Api-Key", auto_error=False)


# ============================================================
#  UNDERWRITING ENDPOINT (unchanged)
# ============================================================
@router.post("/underwrite")
async def underwrite(
    request: UnderwriteRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
    api_key: str = Security(api_key_header),
):
    """
    Universal Polymorphic Underwriting Endpoint.
    """
    manual = await route_to_product(request, db)
    if not manual:
        raise HTTPException(
            status_code=404,
            detail="No matching product found. Please specify a product_type or describe your needs.",
        )

    if not manual.compiled_rules:
        raise HTTPException(
            status_code=503,
            detail="Product rules are still being compiled. Please try again in a moment.",
        )

    decision = await execute_underwriting(request, manual)

    if decision.status == "approved":
        decision.policy_number = generate_policy_number(manual.product_type)

        partner_user = None
        if api_key:
            partner_user = await get_user_by_api_key(api_key, db)

        new_policy = Policy(
            policy_number=decision.policy_number,
            product_type=manual.product_type,
            status="pending_payment",
            holder_name=request.holder_name or f"Anonymous Applicant ({request.age})",
            holder_email=request.holder_email,
            holder_age=request.age,
            coverage_blocks=json.dumps([c.id for c in request.coverage_selection]),
            premium_monthly=decision.premium_monthly,
            premium_annual=decision.premium_annual,
            tenant_id="admin@heirs-life.com" if "life" in manual.product_type.lower()
                      else "admin@heirs-gadget.com" if "gadget" in manual.product_type.lower()
                      else "admin@heirs-general.com",
            partner_id=partner_user.id if partner_user else None,
            manual_id=manual.id
        )
        db.add(new_policy)
        await db.commit()
        await db.refresh(new_policy)

    accept_header = http_request.headers.get("accept", "application/json")
    if "soap+xml" in accept_header or "text/xml" in accept_header:
        return create_soap_response(decision.model_dump(mode="json"))

    return decision


# ============================================================
#  MOCK PAYMENT ENDPOINT  
# ============================================================
@router.post("/pay")
async def mock_pay(
    policy_number: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Mock payment endpoint. Simulates a Paystack-style payment.
    No real money moves — generates a fake reference and activates the policy.
    """
    result = await db.execute(select(Policy).where(Policy.policy_number == policy_number))
    policy = result.scalars().first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    if policy.status == "active":
        return {
            "status": "already_paid",
            "message": "This policy is already active.",
            "policy_number": policy_number,
        }

    # Simulate payment
    ref = f"PAY-SIM-{uuid.uuid4().hex[:8].upper()}"
    amount = policy.premium_annual or (policy.premium_monthly or 0) * 12

    # Commission splitting
    partner_commission = amount * 0.15 if policy.partner_id else 0
    platform_fee = amount * 0.05
    insurer_share = amount - partner_commission - platform_fee

    payment = Payment(
        policy_id=policy.id,
        amount=amount,
        currency="NGN",
        insurer_share=round(insurer_share, 2),
        partner_commission=round(partner_commission, 2),
        platform_fee=round(platform_fee, 2),
        gateway="paystack_sim",
        gateway_reference=ref,
        status="success",
    )
    db.add(payment)

    # Activate policy
    policy.status = "active"
    await db.commit()

    return {
        "status": "success",
        "message": f"Payment of ₦{amount:,.2f} simulated successfully.",
        "policy_number": policy_number,
        "gateway_reference": ref,
        "receipt": {
            "amount": amount,
            "insurer_share": round(insurer_share, 2),
            "partner_commission": round(partner_commission, 2),
            "platform_fee": round(platform_fee, 2),
            "currency": "NGN",
        }
    }


# ============================================================
#  AGENTIC CHAT ENDPOINT
# ============================================================

CONSUMER_ACTIONS = """
You can perform these actions for CONSUMERS:
- show_products: Show available insurance products
- start_quote: Start an insurance quote (needs age, product_type). Ask the user for missing info.
- show_policies: Show the user's policies (needs holder_email)
- initiate_payment: Initiate payment for a policy (needs policy_number)
- text_reply: Just answer a question conversationally
"""

PARTNER_ACTIONS = """
You can perform these actions for PARTNERS:
- show_dashboard: Show partner metrics (total policies sold, commission earned)
- rotate_api_key: Generate a new API key for the partner
- show_widget_code: Show the embeddable widget code
- text_reply: Just answer a question conversationally
"""

AGENTIC_SYSTEM_PROMPT = """
You are InsurBridge AI, a full-service insurance assistant.
You help users complete tasks through conversation.

The user's role is: {role}

{role_actions}

Available Products: Life Insurance (life), Auto Insurance (auto), Gadget Insurance (gadget)

RULES:
1. Always respond with VALID JSON only. No markdown, no extra text.
2. Use this exact format:
{{
  "action": "<action_name>",
  "message": "<friendly message to the user>",
  "data": {{}},
  "suggestions": ["suggestion 1", "suggestion 2"]
}}
3. For "start_quote" action, include in data: {{"age": <number>, "product_type": "<type>"}}
   - If the user hasn't provided age or product type, set action to "text_reply" and ASK for the missing info.
4. For "initiate_payment", include in data: {{"policy_number": "<number>"}}
5. For "show_policies", include in data: {{"holder_email": "<email>"}} or empty if unknown.
6. For "text_reply", just put your answer in "message".
7. Keep suggestions relevant — 2-3 short clickable phrases.
8. Tone: {tone}

IMPORTANT: Output ONLY the JSON object. No other text before or after.
"""


async def execute_chat_action(action: str, data: dict, role: str, db: AsyncSession) -> dict:
    """Execute an action detected by the LLM and return enriched data."""

    if action == "show_products":
        return {
            "products": [
                {"id": p.id, "name": p.name, "description": p.description, "base_price": p.base_price, "icon": p.icon}
                for p in AVAILABLE_PRODUCTS
            ]
        }

    elif action == "start_quote":
        age = data.get("age", 30)
        product_type = data.get("product_type", "life")
        
        request = UnderwriteRequest(
            age=age,
            product_type=product_type,
            role=role,
            holder_name=data.get("holder_name", f"Chat User ({age})"),
            coverage_selection=[]
        )
        manual = await route_to_product(request, db)
        if not manual or not manual.compiled_rules:
            return {"error": f"Product '{product_type}' not found or not ready."}

        decision = await execute_underwriting(request, manual)

        # If approved, create policy
        policy_number = None
        if decision.status == "approved":
            policy_number = generate_policy_number(manual.product_type)
            decision.policy_number = policy_number
            
            new_policy = Policy(
                policy_number=policy_number,
                product_type=manual.product_type,
                status="pending_payment",
                holder_name=data.get("holder_name", f"Chat User ({age})"),
                holder_email=data.get("holder_email"),
                holder_age=age,
                coverage_blocks="[]",
                premium_monthly=decision.premium_monthly,
                premium_annual=decision.premium_annual,
                tenant_id="admin@heirs-life.com" if "life" in manual.product_type.lower()
                          else "admin@heirs-gadget.com" if "gadget" in manual.product_type.lower()
                          else "admin@heirs-general.com",
                manual_id=manual.id
            )
            db.add(new_policy)
            await db.commit()

        return {
            "quote": {
                "status": decision.status,
                "premium_monthly": decision.premium_monthly,
                "premium_annual": decision.premium_annual,
                "reason": decision.reason,
                "summary": decision.plain_english_summary,
                "policy_number": policy_number,
                "product_type": manual.product_type,
            }
        }

    elif action == "show_policies":
        email = data.get("holder_email")
        if email:
            result = await db.execute(select(Policy).where(Policy.holder_email == email))
        else:
            result = await db.execute(select(Policy).order_by(Policy.bound_at.desc()).limit(10))
        
        policies = result.scalars().all()
        return {
            "policies": [
                {
                    "policy_number": p.policy_number,
                    "product_type": p.product_type,
                    "status": p.status,
                    "holder_name": p.holder_name,
                    "premium_monthly": p.premium_monthly,
                    "premium_annual": p.premium_annual,
                }
                for p in policies
            ]
        }

    elif action == "initiate_payment":
        policy_number = data.get("policy_number")
        if not policy_number:
            return {"error": "No policy number provided."}
        
        result = await db.execute(select(Policy).where(Policy.policy_number == policy_number))
        policy = result.scalars().first()
        if not policy:
            return {"error": f"Policy {policy_number} not found."}
        
        return {
            "payment": {
                "policy_number": policy.policy_number,
                "amount": policy.premium_annual or (policy.premium_monthly or 0) * 12,
                "currency": "NGN",
                "status": policy.status,
            }
        }

    elif action == "show_dashboard":
        result = await db.execute(select(Policy).limit(50))
        policies = result.scalars().all()
        total = len(policies)
        active = sum(1 for p in policies if p.status == "active")
        pending = sum(1 for p in policies if p.status == "pending_payment")
        total_premium = sum(p.premium_annual or 0 for p in policies)
        
        return {
            "dashboard": {
                "total_policies": total,
                "active_policies": active,
                "pending_policies": pending,
                "total_premium_value": total_premium,
                "currency": "NGN"
            }
        }

    elif action == "rotate_api_key":
        return {
            "api_key_action": "rotate",
            "message": "To rotate your API key, use the Integration Center in the portal sidebar, or call POST /api/v1/partners/api-key/rotate with your auth token."
        }

    elif action == "show_widget_code":
        return {
            "widget_code": '''<div id="insurbridge-widget"></div>
<script src="https://cdn.insurbridge.ai/widget.js" 
        data-partner-id="YOUR_EMAIL" 
        data-key="YOUR_API_KEY">
</script>'''
        }

    return {}


@router.post("/chat")
async def agentic_chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Agentic chat endpoint. Detects user intent, executes actions, and returns
    structured responses with action cards for the frontend.
    Supports conversation history and context-aware responses.
    """
    from app.core.llm import get_llm
    from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
    from app.services.underwriting import get_all_manuals, route_to_product

    llm = get_llm()
    
    start_time = time.time()
    chat_log = ChatLog(
        role=request.role,
        message=request.message,
        model="gemini-2.0-flash-lite",
        status="pending"
    )

    role = request.role
    role_actions = CONSUMER_ACTIONS if role in ("consumer", "agent") else PARTNER_ACTIONS
    tone = "friendly, simple, no jargon" if role == "consumer" else "professional, concise"

    # RAG / Context Injection
    # Try to determine if the user is asking about a specific product type
    # We fake an UnderwriteRequest just for routing
    rag_context = ""
    try:
        # We assume default age just for routing purposes
        routing_req = UnderwriteRequest(
            age=30, 
            natural_language_query=request.message,
            role=role,
            product_type=None
        )
        manual = await route_to_product(routing_req, db)
        if manual:
            rag_context = f"\nRelevant Product Context: The user is likely asking about {manual.product_type} insurance.\n"
    except Exception:
        pass

    system_prompt = AGENTIC_SYSTEM_PROMPT.format(
        role=role,
        role_actions=role_actions,
        tone=tone,
    ) + rag_context

    # Build message history
    messages = [SystemMessage(content=system_prompt)]
    
    # Add history (last 5 messages to save context window)
    for msg in request.history[-10:]:
        content = msg.get("content", "")
        if msg.get("role") == "model" or msg.get("role") == "ai":
             messages.append(AIMessage(content=content))
        else:
             messages.append(HumanMessage(content=content))

    # Add current message
    messages.append(HumanMessage(content=request.message))

    try:
        response = await llm.ainvoke(messages)
        raw = normalize_content(response.content)
    except Exception as e:
        logger.error(f"Agentic chat LLM failed: {e}")
        return {
            "message": "I'm having connection issues. Please try again.",
            "action": "text_reply",
            "data": {},
            "suggestions": ["Tell me about life insurance", "Show products"],
        }

    # Parse the LLM JSON response
    try:
        # Clean up markdown if present
        clean = raw.strip()
        if clean.startswith("```json"):
            clean = clean[7:]
        if clean.startswith("```"):
            clean = clean[3:]
        if clean.endswith("```"):
            clean = clean[:-3]
        
        parsed = json.loads(clean.strip())
    except (json.JSONDecodeError, Exception) as e:
        logger.warning(f"Failed to parse agentic JSON: {e}. Raw: {raw[:200]}")
        # Fallback: treat as text_reply
        parsed = {
            "action": "text_reply",
            "message": raw,
            "data": {},
            "suggestions": [],
        }

    action = parsed.get("action", "text_reply")
    ai_message = parsed.get("message", "")
    action_data = parsed.get("data", {})
    suggestions = parsed.get("suggestions", [])

    # Execute the action if it's not just a text reply
    enriched_data = {}
    if action != "text_reply":
        try:
            enriched_data = await execute_chat_action(action, action_data, role, db)
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            enriched_data = {"error": str(e)}

    response_payload = {
        "message": ai_message,
        "action": action,
        "data": {**action_data, **enriched_data},
        "suggestions": suggestions,
        "product_matched": action_data.get("product_type"),
        "role": role,
    }

    # Logging
    try:
        chat_log.status = "success"
        chat_log.response = ai_message
        chat_log.action = action
        chat_log.latency_ms = (time.time() - start_time) * 1000
        db.add(chat_log)
        await db.commit()
        logger.info(f"CHAT_LOG: Role={role} Msg='{request.message[:50]}...' Action={action} Latency={chat_log.latency_ms:.0f}ms Status=success")
    except Exception as e:
        logger.error(f"Failed to save chat log: {e}")

    return response_payload


# ============================================================
#  D2C ENDPOINTS (products, calculator)
# ============================================================
from app.schemas.underwrite import CoverageBlock, CalculatorRequest

AVAILABLE_PRODUCTS = [
    CoverageBlock(
        id="life_basic",
        name="Life Protection",
        description="Lump sum payout to your beneficiaries.",
        base_price=5000.0,
        icon="Heart"
    ),
    CoverageBlock(
        id="critical_illness",
        name="Critical Illness",
        description="Coverage for cancer, stroke, and heart attack.",
        base_price=3000.0,
        icon="Activity"
    ),
    CoverageBlock(
        id="accidental_death",
        name="Accidental Death",
        description="Double payout for accidental passing.",
        base_price=1500.0,
        icon="Zap"
    ),
    CoverageBlock(
        id="funeral_cover",
        name="Funeral Expenses",
        description="Immediate cash for funeral costs.",
        base_price=1000.0,
        icon="Umbrella"
    )
]

@router.get("/products")
async def get_products():
    """Public endpoint to list available coverage blocks."""
    return AVAILABLE_PRODUCTS


@router.post("/calculate-premium")
async def calculate_premium(request: CalculatorRequest):
    """Calculate premium based on age and selected coverage."""
    total = 0.0
    selected_ids = set(request.selected_coverage)
    for product in AVAILABLE_PRODUCTS:
        if product.id in selected_ids:
            total += product.base_price

    if request.age > 30:
        age_load = (request.age - 30) * 100
        total += age_load

    return {"premium": total}
