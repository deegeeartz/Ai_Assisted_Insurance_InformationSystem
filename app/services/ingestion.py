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
        {text[:30000]}  # Truncate to avoid context limit if needed
        
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
            ]
        }}
        
        Only output valid JSON. Do not include markdown formatting like ```json.
        """
        
        try:
            response = llm.invoke([HumanMessage(content=prompt)])
            compiled_json = response.content.replace("```json", "").replace("```", "").strip()
            
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
        
    except Exception as e:
        logger.error(f"Error processing manual {manual_id}: {e}")
