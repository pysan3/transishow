from pydantic import EmailStr
from sqlalchemy import Boolean, Column, Integer, String

from core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Column | int = Column(Integer, primary_key=True, index=True)
    email: Column | EmailStr = Column(String, nullable=False, unique=True, index=True)
    username = Column(String, nullable=False)
    password: Column | str = Column(String, nullable=False)
    email_verified: Column | bool = Column(Boolean, default=False)
    is_active: Column | bool = Column(Boolean, default=False)
    is_admin: Column | bool = Column(Boolean, default=False)


class Token(Base):
    __tablename__ = "tokens"
    id: Column | int = Column(String, primary_key=True)
