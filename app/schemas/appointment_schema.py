from pydantic import BaseModel, field_validator
from datetime import date, time
from typing import Literal
from app.core.enums import AppointmentStatus


class AppointmentCreate(BaseModel):
    doctor_id: int
    appointment_date: date
    appointment_time: time
    medical_service: str
    reason: str

    @field_validator("appointment_time", mode="before")
    @classmethod
    def normalize_time(cls, v):
        if isinstance(v, str):
            parts = v.split(":")
            return time(int(parts[0]), int(parts[1]))
        if isinstance(v, time):
            return time(v.hour, v.minute)
        return v

    class Config:
        from_attributes = True


class PaginationResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int

    class Config:
        from_attributes = True


class PatientAppointmentsResponse(BaseModel):
    doctor_id: int
    appointment_id: int
    appointment_date: date
    appointment_time: time
    medical_service: str
    status: str

    class Config:
        from_attributes = True


class PatientAppointmentListResponse(PaginationResponse):
    appointments: list[PatientAppointmentsResponse]

    class Config:
        from_attributes = True


class DoctorAppointmentsResponse(BaseModel):
    patient_id: int
    appointment_id: int
    appointment_date: date
    appointment_time: time
    medical_service: str
    reason: str
    status: str

    class Config:
        from_attributes = True


class DoctorAppointmentListResponse(PaginationResponse):
    appointments: list[DoctorAppointmentsResponse]

    class Config:
        from_attributes = True


class AppointmentUpdate(BaseModel):
    appointment_date: date | None = None
    appointment_time: time | None = None
    reason: str | None = None

    @field_validator("appointment_time", mode="before")
    @classmethod
    def normalize_time(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            parts = v.split(":")
            return time(int(parts[0]), int(parts[1]))
        if isinstance(v, time):
            return time(v.hour, v.minute)
        return v

    class Config:
        from_attributes = True


class AppointmentStatusUpdate(BaseModel):
    """Doctor-side status transition payload."""
    status: Literal[
        AppointmentStatus.CONFIRMED,
        AppointmentStatus.COMPLETED,
        AppointmentStatus.REJECTED,
        AppointmentStatus.CANCELLED,
    ]

    class Config:
        from_attributes = True
