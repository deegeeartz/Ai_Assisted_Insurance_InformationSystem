from sqlalchemy import Column, Integer, String, Text, Float, DateTime
from sqlalchemy.sql import func
from app.db.base import Base

class ChatLog(Base):
    __tablename__ = "chat_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    role = Column(String)  # consumer/agent/partner
    message = Column(Text)
    response = Column(Text)
    action = Column(String)
    latency_ms = Column(Float)
    model = Column(String)
    status = Column(String) # success/error
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
