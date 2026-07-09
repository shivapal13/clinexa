from app.core.database import Base
from sqlalchemy import Column,String,Integer,ForeignKey,DATE,Time,DateTime,Enum
from sqlalchemy.sql import func
from app.models import patient_model,doctor_model
from app.core.enums import AppointmentStatus

class Appointment(Base):
    __tablename__='appointments'

    appointment_id=Column(Integer,primary_key=True,nullable=False)

    patient_id=Column(Integer,ForeignKey("Patient_Profiles.patient_id"),nullable=False)

    doctor_id=Column(Integer,ForeignKey("doctor_profiles.doctor_id"),nullable=False)

    medical_service=Column(String,nullable=False)

    reason=Column(String,nullable=False)

    appointment_date=Column(DATE,nullable=False)

    appointment_time=Column(Time,nullable=False)

    status=Column(Enum(AppointmentStatus),nullable=False,default=AppointmentStatus.PENDING)

    created_at=Column(DateTime(timezone=True),server_default=func.now())