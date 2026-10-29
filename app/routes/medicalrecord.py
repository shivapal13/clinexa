from fastapi import HTTPException, status, Depends, APIRouter
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models import medicalrecord_model, doctor_model, patient_model, appointment_model
from app.schemas import medicalrecord_schema
from app.core.database import get_db
from app.core import security
from app.core.enums import AppointmentStatus

router = APIRouter(prefix="/medicalreport", tags=["Medical Reports"])


# ---------------------------------------------------------------------------
# POST /medicalreport/{appointment_id}  — doctor creates a record
# ---------------------------------------------------------------------------
@router.post(
    "/{appointment_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=medicalrecord_schema.DoctorMedicalRecordResponse,
)
def CreateReport(
    appointment_id: int,
    medical_report: medicalrecord_schema.CreateMedicalRecord,
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user),
):
    if current_user.role != "Doctor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    doctor_profile = (
        db.query(doctor_model.Doctor)
        .filter(doctor_model.Doctor.user_id == current_user.id)
        .first()
    )
    if doctor_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")

    appointment = (
        db.query(appointment_model.Appointment)
        .filter(appointment_model.Appointment.appointment_id == appointment_id)
        .first()
    )
    if appointment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found"
        )

    if appointment.doctor_id != doctor_profile.doctor_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    if appointment.status != AppointmentStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Medical report can only be created for completed appointments",
        )

    existing_report = (
        db.query(medicalrecord_model.MedicalRecord)
        .filter(medicalrecord_model.MedicalRecord.appointment_id == appointment_id)
        .first()
    )
    if existing_report:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Medical report already exists"
        )

    # FIX: use correct column names — clinical_notes / follow_up_date
    new_report = medicalrecord_model.MedicalRecord(
        appointment_id=appointment.appointment_id,
        patient_id=appointment.patient_id,
        doctor_id=appointment.doctor_id,
        diagnosis=medical_report.diagnosis,
        symptoms=medical_report.symptoms,
        clinical_notes=medical_report.clinical_notes,
        follow_up_date=medical_report.follow_up_date,
    )

    db.add(new_report)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Medical report already exists for this appointment",
        ) from exc
    db.refresh(new_report)

    return new_report


# ---------------------------------------------------------------------------
# GET /medicalreport/doctor  — all records for the logged-in doctor
# ---------------------------------------------------------------------------
@router.get(
    "/doctor",
    response_model=list[medicalrecord_schema.DoctorMedicalRecordResponse],
)
def ViewDoctorMedicalRecords(
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user),
):
    if current_user.role != "Doctor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    doctor_profile = (
        db.query(doctor_model.Doctor)
        .filter(doctor_model.Doctor.user_id == current_user.id)
        .first()
    )
    if doctor_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")

    return (
        db.query(medicalrecord_model.MedicalRecord)
        .filter(medicalrecord_model.MedicalRecord.doctor_id == doctor_profile.doctor_id)
        .all()
    )


# ---------------------------------------------------------------------------
# GET /medicalreport/doctor/{medical_record_id}  — single record for a doctor
# ---------------------------------------------------------------------------
@router.get(
    "/doctor/{medical_record_id}",
    response_model=medicalrecord_schema.DoctorMedicalRecordResponse,
)
def ViewDoctorMedicalRecordById(
    medical_record_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user),
):
    if current_user.role != "Doctor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    doctor_profile = (
        db.query(doctor_model.Doctor)
        .filter(doctor_model.Doctor.user_id == current_user.id)
        .first()
    )
    if doctor_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")

    # FIX: was MedicalRecord.record_id — correct column is medical_record_id
    medical_record = (
        db.query(medicalrecord_model.MedicalRecord)
        .filter(
            medicalrecord_model.MedicalRecord.doctor_id == doctor_profile.doctor_id,
            medicalrecord_model.MedicalRecord.medical_record_id == medical_record_id,
        )
        .first()
    )
    if medical_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Medical record not found"
        )

    return medical_record


# ---------------------------------------------------------------------------
# PATCH /medicalreport/{medical_record_id}  — doctor updates a record
# ---------------------------------------------------------------------------
@router.patch("/{medical_record_id}")
def UpdateMedicalReport(
    medical_record_id: int,
    update_data: medicalrecord_schema.UpdateMedicalRecord,
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user),
):
    if current_user.role != "Doctor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    doctor_profile = (
        db.query(doctor_model.Doctor)
        .filter(doctor_model.Doctor.user_id == current_user.id)
        .first()
    )
    if doctor_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")

    # FIX: was MedicalRecord.record_id
    medical_record = (
        db.query(medicalrecord_model.MedicalRecord)
        .filter(medicalrecord_model.MedicalRecord.medical_record_id == medical_record_id)
        .first()
    )
    if medical_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Medical record not found"
        )

    if medical_record.doctor_id != doctor_profile.doctor_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    update_dict = update_data.model_dump(exclude_unset=True)
    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update",
        )

    for key, value in update_dict.items():
        setattr(medical_record, key, value)

    db.commit()
    db.refresh(medical_record)

    return medical_record


# ---------------------------------------------------------------------------
# GET /medicalreport/patient  — all records for the logged-in patient
# ---------------------------------------------------------------------------
@router.get(
    "/patient",
    response_model=list[medicalrecord_schema.PatientMedicalRecordResponse],
)
def ViewPatientRecords(
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user),
):
    if current_user.role != "Patient":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    patient_profile = (
        db.query(patient_model.Patient)
        .filter(patient_model.Patient.user_id == current_user.id)
        .first()
    )
    if patient_profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found"
        )

    records = (
        db.query(medicalrecord_model.MedicalRecord)
        .filter(
            medicalrecord_model.MedicalRecord.patient_id == patient_profile.patient_id
        )
        .all()
    )
    return records


# ---------------------------------------------------------------------------
# GET /medicalreport/{medical_record_id}  — single record for a patient
# ---------------------------------------------------------------------------
@router.get(
    "/{medical_record_id}",
    response_model=medicalrecord_schema.PatientMedicalRecordResponse,
)
def ViewPatientRecordById(
    medical_record_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user),
):
    if current_user.role != "Patient":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    patient_profile = (
        db.query(patient_model.Patient)
        .filter(patient_model.Patient.user_id == current_user.id)
        .first()
    )
    if patient_profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found"
        )

    # FIX: was MedicalRecord.record_id
    record = (
        db.query(medicalrecord_model.MedicalRecord)
        .filter(
            medicalrecord_model.MedicalRecord.medical_record_id == medical_record_id
        )
        .first()
    )
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Medical record not found"
        )

    if record.patient_id != patient_profile.patient_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    return record
