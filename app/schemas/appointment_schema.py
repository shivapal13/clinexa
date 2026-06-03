from pydantic import BaseModel
from datetime import date,time


class AppointmentCreate(BaseModel):
    doctor_id:int
    medical_service:str
    reason:str | None=None
    appointment_date:date
    appointment_time:time

    class Config:
        from_attributes = True


class AppointmentsResponse(BaseModel):
    doctor_id:int
    apppointment_id:int
    medical_service:str
    reason:str
    appointment_date:date
    appointment_time:time
    status:str  

    class Config:
        from_attributes = True

class AppointmentsUpdate(BaseModel):

    status:str

    class Config:
        from_attributes=True


class UpdateAppointment(BaseModel):
    appointment_date:date
    appointment_time:time
    reason:str 

    class Config:
        from_attributes=True  
          
        
