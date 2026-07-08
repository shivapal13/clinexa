from pydantic import BaseModel
from datetime import date,time

class AppointmentCreate(BaseModel):
    doctor_id:int
    appointment_date:date
    appointment_time:time
    medical_service:str 
    reason:str
    class Config:
        from_attributes = True

class PaginationResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    
    class Config:
        from_attributes = True

class PatientAppointmentsResponse(PaginationResponse):
    doctor_id:int
    appointment_id:int
    specialisation:str
    appointment_date:date
    appointment_time:time
    medical_service:str
    status:str  

    class Config:
        from_attributes = True
class PatientAppointmentListResponse(PaginationResponse):
    appointments:list[PatientAppointmentsResponse]

    class Config:
     from_attributes = True
    
class DoctorAppointmentsResponse(BaseModel):
    patient_id:int
    appointment_id:int
    appointment_date:date
    appointment_time:time
    medical_service:str
    reason:str
    status:str  

    class Config:
        from_attributes = True

class DoctorAppointmentListResponse(PaginationResponse):
    appointments:list[DoctorAppointmentsResponse]
    
    class Config:
     from_attributes = True

class AppointmentUpdate(BaseModel):
    appointment_date: date | None = None
    appointment_time: time | None = None
    reason: str | None = None

    class Config:
        from_attributes=True

          
        
