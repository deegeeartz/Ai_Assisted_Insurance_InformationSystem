from sqlalchemy import Column, Integer, String, DateTime, Boolean, LargeBinary
from sqlalchemy.sql import func
from app.db.base import Base

class UnderwritingManual(Base):
    __tablename__ = "underwriting_manuals"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    version = Column(String, default="v1")
    product_type = Column(String, index=True) # e.g., "Life", "Auto"
    is_active = Column(Boolean, default=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # In a real production system, we'd store the path to S3.
    # For this hackathon/prototype, we'll store the ENCRYPTED blob directly 
    # or the path to the encrypted file on disk. Let's store path for scalability.
    encrypted_file_path = Column(String)
    encryption_key_id = Column(String) # Reference to the key used (if using a KMS)
    
    # Liquid Logic: The AI-compiled JSON ruleset
    compiled_rules = Column(String) # Storing as JSON string for simplicity with SQLite/Postgres compatibility in proto

