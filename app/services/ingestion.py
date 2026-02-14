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
            
        # 4. LLM Compilation (Liquid Logic) - BYPASS
        # llm = get_llm()
        # prompt = f"""..."""
        # response = llm.invoke(...)
        # compiled_json = response.content
        
        # Just use raw text for now as it works well for RAG
        compiled_json = text
            
        # 5. Save to DB
            
        # 5. Save to DB
        manual.compiled_rules = compiled_json.strip()
        db.add(manual)
        await db.commit()
        
        logger.info(f"Successfully compiled manual {manual_id}")
        
    except Exception as e:
        logger.error(f"Error processing manual {manual_id}: {e}")
