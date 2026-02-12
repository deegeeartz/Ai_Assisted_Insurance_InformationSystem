from pydantic import BaseModel
from datetime import datetime

class ManualBase(BaseModel):
    product_type: str
    version: str = "v1"

class ManualCreate(ManualBase):
    pass

class ManualResponse(ManualBase):
    id: int
    filename: str
    uploaded_at: datetime
    is_active: bool

    class Config:
        from_attributes = True
