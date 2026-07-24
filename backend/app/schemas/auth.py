from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
class UserRead(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    is_admin: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
