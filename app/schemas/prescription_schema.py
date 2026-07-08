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
    instructions:str | None=None

    class Config:
        from_attributes = True

class PatientPrescriptionResponse(BaseModel):
    prescription_id: int
    medical_record_id: int
    doctor_id: int

    medicine_name: str
    dosage: str
    frequency: str
    duration: str
    instructions: str

    class Config:
        from_attributes = True

class DoctorPrescriptionResponse(BaseModel):
    prescription_id: int
    medicine_name: str
    patient_id:int
    dosage: str
    frequency: str
    duration: str
    instructions: str

    class Config:
        from_attributes = True
      
