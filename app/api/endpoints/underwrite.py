from fastapi import APIRouter, Depends, HTTPException, Request, Security, Query
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.schemas.underwrite import UnderwriteRequest, UnderwriteDecision, ChatRequest
from app.services.underwriting import route_to_product, execute_underwriting
from app.services.protocol_adapter import create_soap_response
from app.services.policy_number import generate_policy_number
from app.services.auth import get_user_by_api_key, get_current_user, get_current_user_optional
from app.models.core import Policy, Payment, User
from app.models.chat_log import ChatLog
from app.models.audit import AuditLog, UnderwritingDecisionLog
from app.services.sla import record_policy_sla_event
from app.services.tenant import policy_tenant_from_product
from app.services.documents import generate_key_facts_token
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


async def kill_switch_active(db: AsyncSession) -> bool:
    """True when a superadmin has enabled the global emergency halt."""
    from app.models.core import PlatformConfig
    res = await db.execute(select(PlatformConfig).where(PlatformConfig.key == "kill_switch"))
    cfg = res.scalars().first()
    return bool(cfg and cfg.value.lower() == "true")


@router.get("/policies/my")
async def get_my_policies(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Authenticated policy history endpoint.
    - Consumer: own policies by holder_email
    - Partner: policies sold by this partner
    - Insurer/Admin/Compliance: tenant-scoped policies
    """
    role = str(current_user.role)
    query = select(Policy)

    if role == "consumer":
        query = query.where(Policy.holder_email == current_user.email)
    elif role == "partner":
        query = query.where(Policy.partner_id == current_user.id)
    elif role in ("insurer", "admin", "compliance_officer"):
        query = query.where(Policy.tenant_id == (current_user.tenant_id or current_user.email))
    else:
        query = query.where(Policy.holder_email == current_user.email)

    result = await db.execute(query.order_by(Policy.bound_at.desc()).limit(limit))
    policies = result.scalars().all()

    return [
        {
            "policy_number": p.policy_number,
            "product_type": p.product_type,
            "status": p.status,
            "holder_name": p.holder_name,
            "holder_email": p.holder_email,
            "premium_monthly": p.premium_monthly,
            "premium_annual": p.premium_annual,
            "bound_at": p.bound_at,
        }
        for p in policies
    ]


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
    if await kill_switch_active(db):
        raise HTTPException(status_code=503, detail="Platform emergency halt. Quoting temporarily disabled by Superadmin.")


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

    partner_user = None
    if api_key:
        partner_user = await get_user_by_api_key(api_key, db)

    decision_log, new_policy = await bind_policy_from_decision(
        decision=decision,
        request=request,
        manual=manual,
        db=db,
        channel="d2c",
        partner_id=partner_user.id if partner_user else None
    )
    
    await db.commit()
    
    if new_policy:
        try:
            await record_policy_sla_event(db=db, policy=new_policy, event_type="policy_created")
        except Exception as error:
            logger.warning(f"SLA policy_created metric update skipped: {error}")
        decision.key_facts_token = generate_key_facts_token(decision.policy_number)

    accept_header = http_request.headers.get("accept", "application/json")
    if "soap+xml" in accept_header or "text/xml" in accept_header:
        # Standard endpoint can return SOAP if requested
        return create_soap_response(decision.model_dump(mode="json"))

    return decision


# ============================================================
#  SOAP UNDERWRITING ENDPOINT
# ============================================================
@router.post("/soap/underwrite")
async def soap_underwrite(
    http_request: Request,
    db: AsyncSession = Depends(get_db),
    api_key: str = Security(api_key_header),
):
    """
    Dedicated SOAP endpoint that explicitly accepts XML request bodies 
    for legacy bank and enterprise partners.
    """
    if await kill_switch_active(db):
        raise HTTPException(status_code=503, detail="Platform emergency halt. Quoting temporarily disabled by Superadmin.")


    from app.services.protocol_adapter import soap_xml_to_dict, create_soap_response
    
    xml_str = await http_request.body()
    try:
        data = soap_xml_to_dict(xml_str.decode('utf-8'))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid SOAP XML: {e}")

    # Extract dynamic root (e.g., <UnderwriteRequest>)
    if not data:
        raise HTTPException(status_code=400, detail="Empty SOAP Body")
        
    root_key = list(data.keys())[0]
    payload = data[root_key]

    # Normalize single-element lists from XML parsing
    cov = payload.get("coverage_selection", [])
    if isinstance(cov, dict):
        # xmltodict parses single elements as dict rather than list of dicts
        cov_item = cov.get("CoverageSelection")
        if isinstance(cov_item, list):
            payload["coverage_selection"] = cov_item
        elif isinstance(cov_item, dict):
            payload["coverage_selection"] = [cov_item]
        else:
            payload["coverage_selection"] = []

    try:
        # Fallbacks for types since XML values arrive as strings
        payload["age"] = int(payload.get("age", 30))
        request_obj = UnderwriteRequest(**payload)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"XML Schema Validation Error: {e}")

    # Run core underwriting logic
    manual = await route_to_product(request_obj, db)
    if not manual:
        return create_soap_response({"status": "error", "message": "No matching product found."})
        
    decision = await execute_underwriting(request_obj, manual)

    partner_user = None
    if api_key:
        partner_user = await get_user_by_api_key(api_key, db)

    decision_log, new_policy = await bind_policy_from_decision(
        decision=decision,
        request=request_obj,
        manual=manual,
        db=db,
        channel="soap",
        partner_id=partner_user.id if partner_user else None
    )
    await db.commit()

    if new_policy:
        try:
            await record_policy_sla_event(db=db, policy=new_policy, event_type="policy_created")
        except Exception as error:
            logger.warning(f"SLA policy_created metric update skipped: {error}")

    return create_soap_response(decision.model_dump(mode="json"))


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
    Uses SELECT ... FOR UPDATE to prevent duplicate payments under concurrency.
    """
    result = await db.execute(
        select(Policy)
        .where(Policy.policy_number == policy_number)
        .with_for_update()
    )
    policy = result.scalars().first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    if policy.status == "active":
        return {
            "status": "already_paid",
            "message": "This policy is already active.",
            "policy_number": policy_number,
            "gateway": "paystack_sim",
        }

    # Simulate payment
    ref = f"PSK_SIM_{uuid.uuid4().hex[:10].upper()}"
    access_code = f"ACCSIM{uuid.uuid4().hex[:12].upper()}"
    authorization_url = f"https://checkout.paystack.com/{access_code}"
    paid_at = datetime.utcnow().isoformat() + "Z"
    amount = policy.premium_annual or (policy.premium_monthly or 0) * 12
    amount_kobo = int(round(amount * 100))

    # Fetch global commission config
    from app.models.core import PlatformConfig
    c_res = await db.execute(select(PlatformConfig).where(PlatformConfig.key == "global_commission_rate"))
    c_cfg = c_res.scalars().first()
    partner_rate = float(c_cfg.value) if c_cfg else 0.10
    
    # Commission splitting
    partner_commission = amount * partner_rate if policy.partner_id else 0
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
    await db.refresh(policy)
    try:
        await record_policy_sla_event(db=db, policy=policy, event_type="policy_activated")
    except Exception as error:
        logger.warning(f"SLA policy_activated metric update skipped: {error}")

    return {
        "status": "success",
        "message": f"Payment of ₦{amount:,.2f} simulated successfully.",
        "policy_number": policy_number,
        "gateway": "paystack_sim",
        "gateway_name": "Paystack (Simulated)",
        "gateway_reference": ref,
        "authorization_url": authorization_url,
        "access_code": access_code,
        "payment_stage": "verified",
        "receipt": {
            "amount": amount,
            "amount_kobo": amount_kobo,
            "insurer_share": round(insurer_share, 2),
            "partner_commission": round(partner_commission, 2),
            "platform_fee": round(platform_fee, 2),
            "currency": "NGN",
        },
        "paystack_like": {
            "status": True,
            "message": "Verification successful (simulated)",
            "data": {
                "authorization_url": authorization_url,
                "access_code": access_code,
                "reference": ref,
                "amount": amount_kobo,
                "currency": "NGN",
                "channel": "card",
                "gateway_response": "Successful",
                "status": "success",
                "paid_at": paid_at,
                "metadata": {
                    "policy_number": policy_number,
                    "product_type": policy.product_type,
                    "simulation": True,
                },
                "customer": {
                    "email": policy.holder_email,
                    "name": policy.holder_name,
                },
            },
        },
        "simulation": {
            "provider": "paystack",
            "country": "NG",
            "mode": "simulated",
            "timeline": [
                {"stage": "initialize", "status": "success"},
                {"stage": "authorize", "status": "success"},
                {"stage": "verify", "status": "success"},
            ],
        },
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
- rotate_api_key: Generate a new API key for the partner and display it
- show_widget_code: Show the embeddable widget code
- show_products: Show available insurance products
- start_quote: Start an insurance quote for a client (needs age, product_type). Ask the user for missing info.
- show_policies: Show the partner's sold policies or a specific client's policies (needs holder_email)
- initiate_payment: Initiate payment for a policy (needs policy_number)
- show_commissions: Show the partner's total earned commissions and wallet balance.
- withdraw_commission: Initiate a withdrawal of commission funds to their bank account.
- text_reply: Just answer a question conversationally
"""

ADMIN_ACTIONS = """
You can perform these actions for SUPERADMINS (God-Mode):
- show_dashboard: Show the global platform dashboard (Total GWP, Total active policies across all tenants)
- show_tenants: List all active insurers on the marketplace
- text_reply: Answer questions conversationally, acknowledging your ultimate platform power
"""

INSURER_ACTIONS = """
You can perform these actions for INSURERS:
- show_dashboard: Show metrics specific only to this insurer
- text_reply: Answer questions conversationally
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
3. For "start_quote" action, include in data: {{"age": <number>, "product_type": "<type>", "holder_name": "<full name>", "holder_email": "<email>", "details": "<all other user details like location, BMI, sum assured, VIN, occupation, etc.>"}}
   - If the user hasn't provided age, product type, full name, or email, set action to "text_reply" and ASK for the missing info. This is mandatory for KYC.
4. For "initiate_payment", include in data: {{"policy_number": "<number>"}}
5. For "show_policies", include in data: {{"holder_email": "<email>"}} or empty if unknown.
6. For "text_reply", just put your answer in "message".
7. Keep suggestions relevant — 2-3 short clickable phrases.
8. Tone: {tone}

IMPORTANT: Output ONLY the JSON object. No other text before or after.
"""


async def execute_chat_action(action: str, data: dict, role: str, db: AsyncSession, user: User = None) -> dict:
    """Execute an action detected by the LLM and return enriched data."""

    if action == "show_products":
        return {
            "products": [
                {"id": p.id, "name": p.name, "description": p.description, "base_price": p.base_price, "icon": p.icon, "insurer_name": p.insurer_name, "category": p.category}
                for p in AVAILABLE_PRODUCTS
            ]
        }

    elif action == "start_quote":
        if await kill_switch_active(db):
            return {"error": "Quoting is temporarily disabled by the platform superadmin."}

        age = data.get("age", 30)
        product_type = data.get("product_type", "life")
        
        req = UnderwriteRequest(
            age=age,
            product_type=product_type,
            role=role,
            holder_name=data.get("holder_name", f"Chat User ({age})"),
            natural_language_query=data.get("details", ""),
            coverage_selection=[]
        )
        manual = await route_to_product(req, db)
        if not manual or not manual.compiled_rules:
            return {"error": f"Product '{product_type}' not found or not ready."}

        decision = await execute_underwriting(req, manual)

        decision_log, new_policy = await bind_policy_from_decision(
            decision=decision,
            request=req,
            manual=manual,
            db=db,
            channel="chat",
            partner_id=user.id if user and user.role == "partner" else None
        )
        await db.commit()

        if new_policy:
            try:
                await record_policy_sla_event(db=db, policy=new_policy, event_type="policy_created")
            except Exception as error:
                logger.warning(f"SLA policy_created metric update skipped: {error}")

        return {
            "quote": {
                "status": decision.status,
                "premium_monthly": decision.premium_monthly,
                "premium_annual": decision.premium_annual,
                "reason": decision.reason,
                "summary": decision.plain_english_summary,
                "policy_number": policy_number,
                "key_facts_token": generate_key_facts_token(policy_number) if policy_number else None,
                "product_type": manual.product_type,
            }
        }

    elif action == "show_policies":
        if not user:
            return {"error": "Please sign in to view your policies."}

        if user.role == "partner":
            # Partners see only policies sold through them; optional email filter
            query = select(Policy).where(Policy.partner_id == user.id)
            email = data.get("holder_email")
            if email:
                query = query.where(Policy.holder_email == email)
        elif user.role in ("admin", "insurer", "compliance_officer"):
            # Privileged roles: email filter is accepted; no email → tenant-scoped list
            query = select(Policy)
            if user.role != "admin":
                query = query.where(Policy.tenant_id == (user.tenant_id or user.email))
            email = data.get("holder_email")
            if email:
                query = query.where(Policy.holder_email == email)
        else:
            # Consumers always see only their own policies — email param ignored
            query = select(Policy).where(Policy.holder_email == user.email)

        result = await db.execute(query.order_by(Policy.bound_at.desc()).limit(15))
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
                "key_facts_token": generate_key_facts_token(policy.policy_number),
            }
        }

    elif action == "show_dashboard":
        if not user:
            return {"error": "Authentication required for dashboard."}
            
        if user.role == "admin":
            from sqlalchemy import func
            gwp_query = await db.execute(select(func.sum(Policy.premium_annual)).where(Policy.status == "active"))
            policies_query = await db.execute(select(func.count(Policy.id)).where(Policy.status == "active"))
            return {
                "dashboard": {
                    "total_policies": policies_query.scalar() or 0,
                    "total_premium_value": gwp_query.scalar() or 0.0,
                    "active_policies": policies_query.scalar() or 0,
                    "currency": "NGN",
                    "mode": "Global God-Mode"
                }
            }
            
        query = select(Policy)
        if user.role == "partner":
            query = query.where(Policy.partner_id == user.id)
        elif user.role == "insurer":
            query = query.where(Policy.tenant_id == user.tenant_id)
            
        result = await db.execute(query.limit(200))
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
                "currency": "NGN",
                "mode": user.role.capitalize()
            }
        }

    elif action == "show_commissions":
        if not user or user.role != "partner":
            return {"error": "Only partners can view commissions."}
            
        result = await db.execute(
            select(Payment).join(Policy).where(Policy.partner_id == user.id, Payment.status == "success")
        )
        payments = result.scalars().all()
        total_earned = sum(p.partner_commission for p in payments)
        return {
            "commissions": {
                "total_earned": total_earned,
                "recent_payouts": 0,
                "currency": "NGN"
            }
        }

    elif action == "withdraw_commission":
        if not user or user.role != "partner":
            return {"error": "Only partners can withdraw commissions."}
        amount = data.get("amount", "all available funds")
        return {
            "withdrawal": {
                "status": "success",
                "message": f"Your withdrawal request for {amount} has been queued! Funds will arrive in your linked GTBank account shortly."
            }
        }

    elif action == "rotate_api_key":
        if not user or user.role != "partner":
            return {"error": "Only partners can rotate API keys."}

        from app.services.auth import generate_api_key
        new_key = generate_api_key()
        user.api_key = new_key
        await db.commit()
        return {
            "api_key_action": "rotate",
            "message": f"Success! Your new integration API key is: \n\n`{new_key}`\n\nPlease copy this now, as it will not be shown again."
        }

    elif action == "show_widget_code":
        return {
            "widget_code": (
                "<!-- An embeddable <script> build of the InsurDrop widget is not "
                "available yet. The widget currently runs standalone at its own "
                "deployment URL and can be linked or iframed from your site. -->"
            )
        }

    elif action == "show_tenants":
        if not user or user.role != "admin":
            return {"error": "Admin access required."}
        from app.models.core import UserRole
        result = await db.execute(
            select(User).where(User.role == UserRole.INSURER)
        )
        insurers = result.scalars().all()
        return {
            "tenants": [
                {
                    "tenant_id": u.tenant_id,
                    "company_name": u.company_name,
                    "email": u.email,
                }
                for u in insurers
            ]
        }

    return {}


@router.post("/chat")
async def agentic_chat(
    request: ChatRequest,
    http_req: Request,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
):
    """
    Agentic chat endpoint. Detects user intent, executes actions, and returns
    structured responses with action cards for the frontend.
    Supports conversation history and context-aware responses.
    Anonymous (widget/D2C guest) requests are treated as consumers.
    """
    from app.core.llm import get_llm
    from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
    from app.services.underwriting import get_all_manuals, route_to_product

    llm = get_llm()

    start_time = time.time()
    chat_log = ChatLog(
        session_id=request.session_id,
        user_email=user.email if user else None,
        role=request.role,
        message=request.message,
        model="gemini-3.6-flash",
        status="pending"
    )

    # Determine real role from token if authenticated.
    # Unauthenticated requests are always treated as "consumer" regardless of
    # what request.role claims — prevents role spoofing via the request body.
    if user:
        role = user.role.value if hasattr(user.role, 'value') else str(user.role)
    else:
        role = "consumer"

    if role == "admin":
        role_actions = ADMIN_ACTIONS
        tone = "authoritative, technical, god-mode"
    elif role == "insurer":
        role_actions = INSURER_ACTIONS
        tone = "professional, analytical"
    elif role in ("partner", "agent"):
        role_actions = PARTNER_ACTIONS
        tone = "professional, concise"
    else:
        role_actions = CONSUMER_ACTIONS
        tone = "friendly, simple, no jargon"

    # If the client didn't send any history but gave a session_id, reconstruct
    # history from the DB so the conversation survives page refreshes.
    history_to_use = request.history
    if not history_to_use and request.session_id:
        try:
            prev_logs_result = await db.execute(
                select(ChatLog)
                .where(ChatLog.session_id == request.session_id)
                .order_by(ChatLog.timestamp.asc())
                .limit(10)
            )
            prev_logs = prev_logs_result.scalars().all()
            if prev_logs:
                history_to_use = []
                for log in prev_logs:
                    if log.message:
                        history_to_use.append({"role": "user", "content": log.message})
                    if log.response:
                        history_to_use.append({"role": "model", "content": log.response})
        except Exception as e:
            logger.warning(f"Could not load session history: {e}")

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

    # Add history (last 10 exchanges to stay within context window)
    for msg in history_to_use[-10:]:
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
            enriched_data = await execute_chat_action(action, action_data, role, db, user)
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            await db.rollback()
            enriched_data = {"error": str(e)}

    response_payload = {
        "message": ai_message,
        "action": action,
        "data": {**action_data, **enriched_data},
        "suggestions": suggestions,
        "product_matched": action_data.get("product_type"),
        "role": role,
        "session_id": request.session_id,
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
        await db.rollback()

    return response_payload


# ============================================================
#  CHAT HISTORY ENDPOINT
# ============================================================

@router.get("/chat/history/{session_id}")
async def get_chat_history(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve the stored conversation history for a session_id.
    Returns turns in chronological order as [{role, content}] pairs
    so the frontend can restore its in-memory history after a refresh.

    Access: admins, sessions whose turns are all anonymous (pre-login),
    or the user who owns the session's messages.
    """
    result = await db.execute(
        select(ChatLog)
        .where(ChatLog.session_id == session_id)
        .order_by(ChatLog.timestamp.asc())
        .limit(20)
    )
    logs = result.scalars().all()

    owner_emails = {log.user_email for log in logs if log.user_email}
    if str(current_user.role) != "admin" and owner_emails and current_user.email not in owner_emails:
        raise HTTPException(status_code=403, detail="Not authorized to view this conversation")

    history = []
    for log in logs:
        if log.message:
            history.append({"role": "user", "content": log.message})
        if log.response:
            history.append({"role": "model", "content": log.response})

    return {"session_id": session_id, "history": history}


# ============================================================
#  D2C ENDPOINTS (products, calculator)
# ============================================================
from app.schemas.underwrite import CoverageBlock, CalculatorRequest

from app.core.products import AVAILABLE_PRODUCTS

@router.get("/products")
async def get_products():
    """Public endpoint to list available coverage blocks."""
    return AVAILABLE_PRODUCTS

@router.get("/products/{product_type}/schema")
async def get_product_schema(product_type: str):
    """
    Returns the dynamic JSON required to underwrite this specific product.
    This allows B2B Partners to generate their own custom frontend forms 
    or dynamically map their CRMs.
    """
    base_schema = {
        "age": "integer (required)",
        "product_type": f"string (must be '{product_type}')",
        "holder_name": "string (optional)",
        "holder_email": "string (optional)",
        "coverage_selection": "array of objects (e.g., [{'id': 'coverage_id', 'amount': 1000}])"
    }

    # Simulate LLM-extracted dynamic requirements based on the manual type
    product = product_type.lower()
    dynamic_requirements = {}
    
    if "life" in product:
        dynamic_requirements = {
            "residency": "string (e.g. Resident of Nigeria)",
            "bmi": "number (e.g. 22.5)",
            "sum_assured": "number (e.g. 5,000,000 NGN)"
        }
    elif "gadget" in product or "device" in product or "screen" in product or "warranty" in product:
        dynamic_requirements = {
            "device_imei": "string (15 digit IMEI)",
            "device_model": "string (e.g. iPhone 15 Pro)",
            "purchase_date": "string YYYY-MM-DD (e.g. 2024-01-15)"
        }
    elif "auto" in product or "motor" in product or "vehicle" in product:
        dynamic_requirements = {
            "vehicle_vin": "string (17 char VIN)",
            "license_plate": "string (e.g. KJA-123AA)",
            "vehicle_usage": "string (Private or Commercial)"
        }
    elif "home" in product or "house" in product or "property" in product:
        dynamic_requirements = {
            "property_address": "string (e.g. 12 Marina, Lagos)",
            "building_type": "string (e.g. Duplex, Apartment)",
            "property_value": "number (e.g. 25,000,000 NGN)"
        }
    else:
        dynamic_requirements = {
            "identification_number": "string (e.g. NIN or Drivers License)",
            "coverage_amount": "number (e.g. 1,000,000 NGN)"
        }
        
    return {
        "product": product_type,
        "base_fields": base_schema,
        "product_specific_fields": dynamic_requirements,
        "notes": "You may also pass 'natural_language_query' to override specific rules dynamically."
    }


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
