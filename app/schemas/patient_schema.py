from pydantic import BaseModel


class PatientProfileCreate(BaseModel):
    age:int
    gender:str
    blood_group:str
    phone_number:str
    address:str

    class Config:
        from_attributes = True

class PatientProfileUpdate(BaseModel):

    age:int | None=None
    gender:str | None=None
    blood_group:str | None=None
    phone_number:str | None=None
    address:str | None=None

    class Config:
        from_attributes=True