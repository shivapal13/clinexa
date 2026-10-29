from app.core.database import Base
from sqlalchemy import Column, String, Integer, ForeignKey, Float, CheckConstraint, Index
from sqlalchemy.orm import relationship


class Doctor(Base):
    __tablename__ = "doctor_profiles"

    __table_args__ = (
        CheckConstraint(
            "verification_status IN ('PENDING', 'VERIFIED', 'REJECTED')",
            name="ck_doctor_verification_status",
        ),
        Index("index_doctor_verification_status", "verification_status"),
        Index("index_doctor_specialisation", "specialisation"),
        Index("index_doctor_specialisation_city", "specialisation", "city"),
    )

    doctor_id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    specialisation = Column(String, nullable=False)
    experience = Column(Integer, nullable=False)
    fees = Column(Float, nullable=False)
    city = Column(String, nullable=False)
    bio = Column(String, nullable=False)
    hospital_name = Column(String, nullable=False)
    license_number = Column(String(128), nullable=True)
    verification_status = Column(
        String(16), nullable=False, default="PENDING", server_default="PENDING"
    )

    recurring_availability = relationship(
        "RecurringAvailability",
        back_populates="doctor",
        cascade="all, delete-orphan",
    )

    custom_availability = relationship(
        "CustomAvailability",
        back_populates="doctor",
        cascade="all, delete-orphan",
    )
