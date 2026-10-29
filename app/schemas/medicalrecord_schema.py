from pydantic import BaseModel
from datetime import date


# FIX: field names now match the actual ORM column names:
#   clinical_notes  (was doctor_notes)
#   follow_up_date  (was follow_up_dates)
#   medical_record_id (was record_id)


class CreateMedicalRecord(BaseModel):
    diagnosis: str
    symptoms: str
    clinical_notes: str | None = None
    follow_up_date: date | None = None

    class Config:
        from_attributes = True


class UpdateMedicalRecord(BaseModel):
    diagnosis: str | None = None
    symptoms: str | None = None
    clinical_notes: str | None = None
    follow_up_date: date | None = None

    class Config:
        from_attributes = True


class PatientMedicalRecordResponse(BaseModel):
    medical_record_id: int
    appointment_id: int
    doctor_id: int
    diagnosis: str
    symptoms: str
    clinical_notes: str | None = None
    follow_up_date: date | None = None

    class Config:
        from_attributes = True


class DoctorMedicalRecordResponse(BaseModel):
    medical_record_id: int
    appointment_id: int
    patient_id: int
    diagnosis: str
    symptoms: str
    clinical_notes: str | None = None
    follow_up_date: date | None = None

    class Config:
        from_attributes = True
