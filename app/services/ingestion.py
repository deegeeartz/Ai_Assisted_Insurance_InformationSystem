from app.core.security import decrypt_data
from app.core.llm import get_llm
from app.models.manual import UnderwritingManual
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from langchain_core.messages import HumanMessage
import pypdf
import io
import json
import logging

logger = logging.getLogger(__name__)


def normalize_llm_content(content):
    """Normalize LLM response content (may be list of dicts in newer langchain)."""
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


async def process_manual_ingestion(manual_id: int, db: AsyncSession):
    try:
        # 1. Fetch Manual
        result = await db.execute(select(UnderwritingManual).where(UnderwritingManual.id == manual_id))
        manual = result.scalars().first()
        if not manual:
            logger.error(f"Manual {manual_id} not found")
            return

        # 2. Read & Decrypt
        with open(manual.encrypted_file_path, "rb") as f:
            encrypted_content = f.read()
        
        decrypted_content = decrypt_data(encrypted_content)
        
        # 3. Extract Text
        text = ""
        if manual.filename.endswith(".txt"):
            text = decrypted_content.decode("utf-8", errors="ignore")
        else:
            # Assume PDF
            pdf_file = io.BytesIO(decrypted_content)
            reader = pypdf.PdfReader(pdf_file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
        # 4. LLM Compilation (Liquid Logic)
        llm = get_llm()
        
        prompt = f"""
        You are an expert Insurance Underwriter.
        
        Analyze the following underwriting manual content and extract a DETERMINISTIC RULESET in JSON format.
        
        MANUAL CONTENT:
        {text[:30000]}
        
        Output a JSON object with this structure:
        {{
            "product_type": "{manual.product_type}",
            "rules": [
                {{
                    "condition": "age < 18",
                    "decision": "declined",
                    "reason": "Minimum age is 18",
                    "logic_type": "eligibility"
                }},
                {{
                    "condition": "bmi > 35",
                    "decision": "referred",
                    "reason": "High BMI requires medical exam",
                    "logic_type": "medical"
                }}
            ],
            "base_premium_rules": "explain how to calculate base premium",
            "modifiers": [
                {{"factor": "smoker", "adjustment": "+50%"}}
            ],
            "slas": {{
                "quote_response_time": "30 seconds",
                "claims_processing_time": "48 hours",
                "policy_issuance_time": "24 hours"
            }}
        }}
        
        Only output valid JSON. Do not include markdown formatting like ```json.
        """
        
        try:
            response = llm.invoke([HumanMessage(content=prompt)])
            raw = normalize_llm_content(response.content)
            compiled_json = raw.replace("```json", "").replace("```", "").strip()
            
            # Validate JSON
            json.loads(compiled_json)
        except Exception as e:
            logger.error(f"LLM Compilation failed: {e}. Falling back to raw text.")
            compiled_json = json.dumps({"raw_text": text})
            
        # 5. Save to DB
        manual.compiled_rules = compiled_json
        db.add(manual)
        await db.commit()
        
        logger.info(f"Successfully compiled manual {manual_id}")

        # 6. Extract SLA commitments
        try:
            from app.services.sla import extract_slas_from_manual
            tenant_id = (
                "admin@heirs-life.com" if "life" in manual.product_type.lower()
                else "admin@heirs-gadget.com" if "gadget" in manual.product_type.lower()
                else "admin@heirs-general.com"
            )
            await extract_slas_from_manual(manual_id, tenant_id, db)
        except Exception as e:
            logger.warning(f"SLA extraction skipped: {e}")
        
    except Exception as e:
        logger.error(f"Error processing manual {manual_id}: {e}")
