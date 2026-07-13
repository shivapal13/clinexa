from sqlalchemy import Column,String,Integer,ForeignKey,Date,Time,DateTime
from datetime import datetime
from app.core.database import Base
from sqlalchemy.types import Text
from sqlalchemy.sql import func


class MedicalRecord(Base):
    __tablename__="medical_record"

    medical_record_id=Column(Integer,primary_key=True,nullable=False)

    patient_id=Column(Integer,ForeignKey("patient_profiles.patient_id"),nullable=False)

    doctor_id=Column(Integer,ForeignKey("doctor_profiles.doctor_id"),nullable=False)

    appointment_id = Column(
    Integer,
    ForeignKey("appointments.appointment_id"),
    nullable=False,
    unique=True
)

    diagnosis=Column(String,nullable=False)

    symptoms=Column(String,nullable=False)

    clinical_notes=Column(Text,nullable=True)

    follow_up_date=Column(Date,nullable=True)

    created_at=Column(DateTime(timezone=True),server_default=func.now())
    

