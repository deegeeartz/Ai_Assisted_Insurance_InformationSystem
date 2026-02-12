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
        
        # 3. Extract Text (PDF)
        pdf_file = io.BytesIO(decrypted_content)
        reader = pypdf.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
            
        # 4. LLM Compilation (Liquid Logic)
        llm = get_llm()
        prompt = f"""
        You are an expert Insurance Underwriter System.
        Your task is to convert the following Insurance Underwriting Manual into a structured JSON Execution Schema.
        
        Extract:
        1. 'eligibility_rules': Rules determining who can buy the policy (e.g. Age limits, Location).
        2. 'pricing_tables': Any rates, factors, or logic for calculating premium.
        3. 'coverage_limits': Maximum/Minimum coverage amounts.
        4. 'slas': Service Level Agreements mentioned (e.g. claims processing time).
        
        Output ONLY valid JSON.
        
        MANUAL CONTENT:
        {text[:500000]} # Truncate to safe limit if huge, though Gemini 1.5 can handle 1M+ tokens
        """
        
        response = llm.invoke([HumanMessage(content=prompt)])
        compiled_json = response.content
        
        # Clean up Markdown code blocks if present
        if "```json" in compiled_json:
            compiled_json = compiled_json.split("```json")[1].split("```")[0]
        elif "```" in compiled_json:
            compiled_json = compiled_json.split("```")[1].split("```")[0]
            
        # 5. Save to DB
        manual.compiled_rules = compiled_json.strip()
        db.add(manual)
        await db.commit()
        
        logger.info(f"Successfully compiled manual {manual_id}")
        
    except Exception as e:
        logger.error(f"Error processing manual {manual_id}: {e}")
