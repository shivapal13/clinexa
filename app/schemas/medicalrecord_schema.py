from pydantic import BaseModel
from datetime  import date


class CreateMedicalRecord(BaseModel):
    diagnosis:str
    symptoms:str
    doctor_notes:str|  None = None
    follow_up_dates :date

    class Config:
        from_attributes=True

class UpdateMedicalRecord(BaseModel):
    diagnosis:str |  None=None
    symptoms:str  | None=None
    doctor_notes:str | None=None
    follow_up_dates:date | None=None

    class Config:
        from_attributes = True
