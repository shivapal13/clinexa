from pydantic import BaseModel,EmailStr
from typing import Optional

class UserRegister(BaseModel):
    name:str
    email:EmailStr
    password:str
    role:str

    class Config:
        from_attributes=True


class UserLogin(BaseModel):
    email:EmailStr
    password:str
    class Config:
        from_attributes=True


class TokenResponse(BaseModel):
    access_token:str
    token_type:str
    class Config:
        from_attributes=True

class TokenData(BaseModel):
    id:Optional[int]=None  

    class Config:
        from_attributes=True      