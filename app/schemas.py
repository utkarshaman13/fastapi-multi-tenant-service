from pydantic import BaseModel, EmailStr
from typing import Optional


class OrgCreate(BaseModel):
    organization_name: str
    email: EmailStr
    password: str


class OrgUpdate(BaseModel):
    organization_name: str
    new_organization_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None


class AdminLogin(BaseModel):
    email: EmailStr
    password: str


class OrgOut(BaseModel):
    organization_name: str
    collection_name: str
    admin_email: EmailStr
