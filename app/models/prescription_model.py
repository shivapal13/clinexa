from app.core.database import Base
from sqlalchemy import Column,String,Integer,Date,Time,DateTime,ForeignKey,Text
from sqlalchemy.sql import func


class Prescription(Base):

    __tablename__="prescription"

    prescription_id=Column(Integer,primary_key=True,nullable=False)

    patient_id=Column(Integer,ForeignKey("Patient_Profiles.patient_id"),nullable=False)

    doctor_id=Column(Integer,ForeignKey("doctor_profiles.doctor_id"),nullable=False)

    medical_record_id=Column(Integer,ForeignKey("medicalrecord.record_id"),nullable=False,unique=True)

    medicine_name=Column(String,nullable=False)

    dosage=Column(String,nullable=False)

    frequency=Column(String,nullable=False)

    duration=Column(String,nullable=False)

    instructions=Column(Text,nullable=True)

    created_at=Column(DateTime(timezone=True),server_default=func.now())



