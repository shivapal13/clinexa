from pydantic import BaseModel, Field, field_validator
from typing import Literal


class DoctorProfileCreate(BaseModel):
    specialisation: str
    experience: int = Field(..., ge=0, le=80, description="Experience in years (0-80)")
    fees: float = Field(..., gt=0, description="Consultation fees must be greater than 0")
    city: str
    bio: str
    hospital_name: str
    license_number: str = Field(min_length=3, max_length=128)

    @field_validator("license_number")
    @classmethod
    def normalize_license_number(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 3:
            raise ValueError("Professional license number must contain at least 3 characters")
        return normalized

    class Config:
        from_attributes = True


class DoctorProfileUpdate(BaseModel):
    specialisation: str | None = None
    experience: int | None = Field(default=None, ge=0, le=80)
    fees: float | None = Field(default=None, gt=0)
    city: str | None = None
    bio: str | None = None
    hospital_name: str | None = None
    license_number: str | None = Field(default=None, min_length=3, max_length=128)

    @field_validator("license_number")
    @classmethod
    def normalize_license_number(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if len(normalized) < 3:
            raise ValueError("Professional license number must contain at least 3 characters")
        return normalized

    class Config:
        from_attributes = True


class DoctorSearchResponse(BaseModel):
    doctor_id: int
    specialisation: str
    experience: int
    fees: float
    city: str
    hospital_name: str
    verification_status: str

    class Config:
        from_attributes = True


class DoctorProfileResponse(DoctorSearchResponse):
    license_number: str | None
    bio: str


class DoctorDashboardResponse(BaseModel):
    upcoming: int
    pending: int
    completed: int
    cancelled: int
    rejected: int

    class Config:
        from_attributes = True


class DoctorVerificationUpdate(BaseModel):
    verification_status: Literal["VERIFIED", "REJECTED"]


class DoctorVerificationReview(BaseModel):
    doctor_id: int
    doctor_name: str
    doctor_email: str
    specialisation: str
    hospital_name: str
    city: str
    license_number: str | None
    verification_status: str

    class Config:
        from_attributes = True


class DoctorAccountForProfile(BaseModel):
    user_id: int
    name: str
    email: str

    class Config:
        from_attributes = True
