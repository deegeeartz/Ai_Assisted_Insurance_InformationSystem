from app.core.llm import get_llm
from app.models.manual import UnderwritingManual
from app.schemas.underwrite import UnderwriteRequest, UnderwriteDecision
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from langchain_core.messages import HumanMessage, SystemMessage
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


_product_router_cache = {}


def normalize_content(content):
    """Normalize LLM response content (handle string vs list)."""
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


async def route_to_product(request: UnderwriteRequest, db: AsyncSession) -> UnderwritingManual | None:
    """
    Intelligent Product Router:
    If product_type is given, use it directly.
    If only natural_language_query is given, use LLM to infer the product type.
    """
    if request.product_type:
        result = await db.execute(
            select(UnderwritingManual)
            .where(UnderwritingManual.product_type == request.product_type)
            .where(UnderwritingManual.is_active == True)
            .order_by(UnderwritingManual.uploaded_at.desc())
        )
        return result.scalars().first()

    # If no product_type, try to infer from natural language
    if request.natural_language_query:
        # Get all available product types
        result = await db.execute(
            select(UnderwritingManual.product_type)
            .where(UnderwritingManual.is_active == True)
            .distinct()
        )
        available_types = [r[0] for r in result.all()]

        if not available_types:
            return None

        # Check cache
        cache_key = request.natural_language_query.strip().lower()
        if cache_key in _product_router_cache:
            inferred_type = _product_router_cache[cache_key]
        else:
            llm = get_llm()
        routing_prompt = f"""
        A user said: "{request.natural_language_query}"
        
        Available insurance product types: {available_types}
        
        Which product type best matches their intent? 
        Reply with ONLY the product type name, nothing else.
        """
        try:
            response = await llm.ainvoke([HumanMessage(content=routing_prompt)])
            inferred_type = normalize_content(response.content).strip()
        except Exception as e:
            logger.error(f"LLM Routing failed: {e}. Falling back to keyword match.")
            # Fallback: Check if any product type is in the query string
            inferred_type = None
            query_lower = request.natural_language_query.lower()
            for p_type in available_types:
                if p_type in query_lower:
                    inferred_type = p_type
                    break
            
            if not inferred_type:
                return None
            
            # Update cache
            _product_router_cache[cache_key] = inferred_type

        result = await db.execute(
            select(UnderwritingManual)
            .where(UnderwritingManual.product_type == inferred_type)
            .where(UnderwritingManual.is_active == True)
            .order_by(UnderwritingManual.uploaded_at.desc())
        )
        return result.scalars().first()

    return None


async def get_all_manuals(db: AsyncSession) -> list[UnderwritingManual]:
    """Retrieve all active underwriting manuals."""
    result = await db.execute(
        select(UnderwritingManual)
        .where(UnderwritingManual.is_active == True)
        .order_by(UnderwritingManual.product_type)
    )
    return result.scalars().all()


async def execute_underwriting(
    request: UnderwriteRequest,
    manual: UnderwritingManual,
) -> UnderwriteDecision:
    """
    The core "Liquid Logic" execution engine.
    Takes the compiled JSON rules and the applicant data,
    and uses the LLM to make a deterministic decision.
    """
    try:
        llm = get_llm()
    except Exception as e:
        logger.error(f"LLM unavailable: {e}")
        return UnderwriteDecision(
            status="referred",
            reason="AI Service Unavailable",
            plain_english_summary="Our AI underwriter is currently offline. Your application has been forwarded to a human for review.",
            timestamp=datetime.now()
        )

    # Build coverage context
    selected_coverage = [c.name for c in request.coverage_selection if c.enabled]
    coverage_str = ", ".join(selected_coverage) if selected_coverage else "All available coverage"

    # Role-based system prompt
    if request.role == "agent":
        role_instruction = """
        You are responding to an INSURANCE AGENT. Include:
        - Technical underwriting codes and references
        - Commission information if available
        - Cross-sell/upsell opportunities
        - Risk flags and notes for the agent's records
        """
    else:
        role_instruction = """
        You are responding to a CONSUMER. Use:
        - Simple, plain English explanations
        - No jargon or technical codes
        - Friendly, reassuring tone
        - Clear next steps
        """

    system_msg = SystemMessage(content=f"""
    You are InsurBridge AI, a deterministic underwriting decision engine.
    You MUST make decisions based ONLY on the compiled JSON rules provided below.
    
    HOW TO EVALUATE:
    1. Iterate through the "rules" array in the COMPILED RULES.
    2. For each rule, evaluate the "condition" against the APPLICANT PROFILE.
    3. If a condition is met, apply the "decision" and "reason".
    4. If the decision is "declined", stop immediately.
    5. If all eligibility rules pass, calculate the premium using "base_premium_rules" and "modifiers".
    
    If the rules don't cover a scenario or data is missing, set status to "referred".
    
    {role_instruction}
    
    COMPILED RULES (JSON):
    {manual.compiled_rules or '{}'}
    
    Respond in this exact JSON format:
    {{
        "status": "approved" | "declined" | "referred",
        "premium_monthly": <number or null>,
        "premium_annual": <number or null>,
        "coverage_details": {{ "block_name": "detail" }},
        "reason": "<specific rule reference>",
        "plain_english_summary": "<consumer-friendly 1-2 sentence summary>",
        "agent_notes": "<technical notes, only if role is agent, otherwise null>",
        "sla_commitments": {{ "metric": "value" }}
    }}
    """)

    human_msg = HumanMessage(content=f"""
    APPLICANT PROFILE:
    - Age: {request.age}
    - Gender: {request.gender or "Not specified"}
    - Occupation: {request.occupation or "Not specified"}
    - Smoker: {request.smoker}
    - Location: {request.location or "Not specified"}
    
    SELECTED COVERAGE: {coverage_str}
    
    ADDITIONAL CONTEXT: {request.natural_language_query or "None"}
    
    Make your underwriting decision now.
    """)

    try:
        response = await llm.ainvoke([system_msg, human_msg])
        raw = normalize_content(response.content)
    except Exception as e:
        logger.error(f"LLM invocation failed: {e}")
        return UnderwriteDecision(
            status="referred",
            reason="AI Technical Difficulty",
            plain_english_summary="We're experiencing a temporary connection issue. Your application has been saved and forwarded to our team.",
            timestamp=datetime.now()
        )

    # Parse JSON from response
    try:
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0]
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0]

        data = json.loads(raw.strip())
    except (json.JSONDecodeError, AttributeError, IndexError) as e:
        logger.warning(f"Could not parse LLM response as JSON: {e}. Raw: {raw[:200]}")
        data = {
            "status": "referred",
            "reason": "System could not parse decision. Manual review required.",
            "plain_english_summary": "We need a human to review your application. We'll get back to you shortly.",
        }

    return UnderwriteDecision(
        status=data.get("status", "referred"),
        premium_monthly=data.get("premium_monthly"),
        premium_annual=data.get("premium_annual"),
        coverage_details=data.get("coverage_details", {}),
        reason=data.get("reason", "No reason provided"),
        plain_english_summary=data.get("plain_english_summary", ""),
        agent_notes=data.get("agent_notes") if request.role == "agent" else None,
        sla_commitments=data.get("sla_commitments", {}),
        timestamp=datetime.now(),
    )
