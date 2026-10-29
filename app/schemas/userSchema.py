from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, Literal
from app.core.enums import UserRole


class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    # Only Patient and Doctor can self-register; Admin accounts must be seeded/promoted
    role: Literal[UserRole.DOCTOR, UserRole.PATIENT]

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip().lower()
        return v

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    is_admin: bool = False

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip().lower()
        return v

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str

    class Config:
        from_attributes = True


class TokenData(BaseModel):
    id: Optional[int] = None

    class Config:
        from_attributes = True
