from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.underwrite import UnderwriteRequest, UnderwriteDecision
from app.services.underwriting import route_to_product, execute_underwriting
from app.services.protocol_adapter import create_soap_response
from app.services.policy_number import generate_policy_number

import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/underwrite")
async def underwrite(
    request: UnderwriteRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Universal Polymorphic Underwriting Endpoint.
    
    Accepts JSON, returns JSON or SOAP/XML based on Accept header.
    Supports:
    - Explicit product_type selection
    - Natural language intent routing
    - Lego-block coverage selection
    - Role-based response (agent vs consumer)
    """

    # 1. Route to the correct product manual
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

    # 2. Execute underwriting decision
    decision = await execute_underwriting(request, manual)

    # 3. Generate policy number if approved
    if decision.status == "approved":
        decision.policy_number = generate_policy_number(manual.product_type)

    # 4. Protocol Adaptation (JSON vs SOAP)
    accept_header = http_request.headers.get("accept", "application/json")

    if "soap+xml" in accept_header or "text/xml" in accept_header:
        return create_soap_response(decision.model_dump(mode="json"))

    # Default: JSON
    return decision


@router.post("/chat")
async def chat_underwrite(
    message: str,
    role: str = "consumer",
    db: AsyncSession = Depends(get_db),
):
    """
    Conversational interface for underwriting.
    
    Users can describe their needs in natural language,
    and the system will route, evaluate, and respond conversationally.
    """
    request = UnderwriteRequest(
        age=0,  # Will be extracted from conversation context in full implementation
        natural_language_query=message,
        role=role,
    )

    manual = await route_to_product(request, db)
    if not manual:
        return {
            "message": "I'd love to help! Could you tell me a bit more about what you're looking for? "
            "For example, are you interested in life insurance, auto coverage, or something else?",
            "products_available": True,
        }

    if not manual.compiled_rules:
        return {
            "message": "I found the right product for you, but I'm still learning its details. "
            "Please try again in a moment!",
        }

    # For the chatbot, use the LLM to generate a conversational response
    from app.core.llm import get_llm
    from langchain_core.messages import HumanMessage, SystemMessage

    llm = get_llm()

    role_tone = "friendly, simple, no jargon" if role == "consumer" else "professional, include technical details"

    try:
        response = llm.invoke([
            SystemMessage(content=f"""
            You are InsurBridge AI, a helpful insurance assistant.
            Tone: {role_tone}.
            
            You have access to these compiled insurance rules:
            {manual.compiled_rules}
            
            Help the user understand their options. If they describe a need,
            suggest specific coverage blocks. If they ask about pricing,
            give estimates based on the rules. Always explain in {role_tone} language.
            """),
            HumanMessage(content=message),
        ])
        content = response.content
    except Exception as e:
        logger.error(f"LLM Chat failed: {e}. Falling back to manual text.")
        # Fallback: Return a snippet of the manual
        snippet = manual.compiled_rules[:500] + "..." if manual.compiled_rules else "No details available."
        content = f"I'm having trouble connecting to my brain right now, but here is what the `{manual.product_type}` manual says:\n\n{snippet}"

    return {
        "message": content,
        "product_matched": manual.product_type,
        "role": role,
    }


# --- D2C Endpoints ---
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
    
    # 1. Base Price Sum
    selected_ids = set(request.selected_coverage)
    for product in AVAILABLE_PRODUCTS:
        if product.id in selected_ids:
            total += product.base_price

    # 2. Age Loading (Simple Logic)
    # If age > 30, add 100 for each year above 30
    if request.age > 30:
        age_load = (request.age - 30) * 100
        total += age_load

    return {"premium": total}
