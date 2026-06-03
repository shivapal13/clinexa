from app.database import Base
from sqlalchemy import Column,String,Boolean,Integer,ForeignKey,Float

class Doctor(Base):
    __tablename__="doctor_profiles"

    doctor_id=Column(Integer,primary_key=True,nullable=False)
    user_id=Column(Integer,ForeignKey("users.id"),nullable=False,unique=True)
    specialisation=Column(String,nullable=False)
    experience=Column(Integer,nullable=False)
    fees=Column(Float,nullable=False)
    city=Column(String,nullable=False)
    bio=Column(String,nullable=False)
    hospital_name=Column(String,nullable=False)

