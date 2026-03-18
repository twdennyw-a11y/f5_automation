from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from models import RoleEnum, RequestTypeEnum, RequestStatusEnum

class UserCreate(BaseModel):
    username: str
    password: str
    role: RoleEnum = RoleEnum.user

class UserResponse(BaseModel):
    id: int
    username: str
    role: RoleEnum
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class RequestCreate(BaseModel):
    request_type: RequestTypeEnum
    target_ip: str
    details: str # We keep it simple as JSON string

class RequestResponse(BaseModel):
    id: int
    user_id: int
    request_type: RequestTypeEnum
    target_ip: str
    details: str
    status: RequestStatusEnum
    created_at: datetime
    updated_at: datetime
    admin_log: Optional[str] = None
    
    class Config:
        from_attributes = True

class RequestUpdateStatus(BaseModel):
    status: RequestStatusEnum
    # details or comments can be added optionally
    
