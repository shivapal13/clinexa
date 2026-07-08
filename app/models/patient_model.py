from app.core.database import Base
from sqlalchemy import Column,String,Integer,Boolean,ForeignKey


class Patient(Base):
    __tablename__="Patient_Profiles"
     
    patient_id=Column(Integer,primary_key=True,nullable=False)
    user_id=Column(Integer,ForeignKey("users.id"),nullable=False,unique=True)
    age=Column(Integer,nullable=False)
    gender=Column(String,nullable=False)
    blood_group=Column(String,nullable=False)
    phone_number=Column(String,nullable=False)
    address=Column(String,nullable=False) 
