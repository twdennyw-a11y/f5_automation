from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from database import Base

class RoleEnum(str, enum.Enum):
    user = "user"
    admin = "admin"

class RequestTypeEnum(str, enum.Enum):
    info_query = "info_query"
    waf_rule = "waf_rule"
    certificate = "certificate"

class RequestStatusEnum(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    completed = "completed"
    failed = "failed"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(Enum(RoleEnum), default=RoleEnum.user)

class F5Request(Base):
    __tablename__ = "f5_requests"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    request_type = Column(Enum(RequestTypeEnum))
    target_ip = Column(String) # For now, allow user to input IP
    details = Column(Text) # JSON string with request specific details
    status = Column(Enum(RequestStatusEnum), default=RequestStatusEnum.pending)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    admin_log = Column(Text, nullable=True) # Output from F5 execution

    user = relationship("User")
