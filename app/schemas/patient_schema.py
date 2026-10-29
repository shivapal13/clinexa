from pydantic import BaseModel, Field
from typing import Literal

BloodGroupType = Literal["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]


class PatientProfileCreate(BaseModel):
    age: int = Field(..., ge=0, le=130, description="Age must be between 0 and 130")
    gender: Literal["Male", "Female", "Other"]
    blood_group: BloodGroupType
    phone_number: str
    address: str

    class Config:
        from_attributes = True


class PatientProfileUpdate(BaseModel):
    age: int | None = Field(None, ge=0, le=130)
    gender: Literal["Male", "Female", "Other"] | None = None
    blood_group: BloodGroupType | None = None
    phone_number: str | None = None
    address: str | None = None

    class Config:
        from_attributes = True


class PatientSearchResponse(BaseModel):
    patient_id: int
    age: int
    gender: str
    blood_group: str
    phone_number: str
    address: str

    class Config:
        from_attributes = True
