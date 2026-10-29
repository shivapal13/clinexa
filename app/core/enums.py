from enum import Enum


class AppointmentStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class UserRole(str, Enum):
    DOCTOR = "Doctor"
    PATIENT = "Patient"
    ADMIN = "Admin"
