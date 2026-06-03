from pydantic import BaseModel

class DoctorProfileCreate(BaseModel):
    specialisation:str
    experience:int
    fees:float
    city:str
    bio:str
    hospital_name:str

    class Config:
        from_attributes = True


class DoctorProfileUpdate(BaseModel):
    specialisation:str | None = None
    experience:int | None = None
    fees:float | None = None
    city:str | None = None
    bio:str | None = None
    hospital_name:str | None = None

    class Config:
        from_attributes = True

class DoctorSearchResponse(BaseModel):
    doctor_id: int
    specialisation: str
    experience: int
    fees: float
    city: str
    hospital_name: str

    class Config:
        from_attributes = True 


class DoctorDashboardResponse(BaseModel):
    upcoming:int
    pending:int
    completed:int
    cancelled:int
    rejected:int

    class Config:
        from_attributes = True                  
