from typing import Any, Dict, List
from pydantic import BaseModel, EmailStr


class EmailSchema(BaseModel):
    emails: List[EmailStr]
    body: Dict[str, Any]


class Token(BaseModel):
    access_token: str
    token_type: str


class LoginDetails(BaseModel):
    email: EmailStr
    password: str


class RefreshDetails(BaseModel):
    refresh_token: str


class ResetPasswordDetails(BaseModel):
    token: str
    password: str
    re_password: str
