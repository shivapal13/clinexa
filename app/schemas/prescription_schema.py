from pydantic import BaseModel


class CreatePrescription(BaseModel):
    medicine_name:str
    dosage:str
    frequency:str
    duration:str
    instructions:str

    class Config:
        from_attributes = True

class updatePrescription(BaseModel):
    medicine_name:str | None=None
    dosage:str | None=None
    frequency:str | None=None
    duration:str | None=None
    instruction:str | None=None

    class Config:
        from_attributes = True
