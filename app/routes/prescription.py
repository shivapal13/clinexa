from fastapi import HTTPException, status, Depends, APIRouter
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.schemas import prescription_schema
from app.models import prescription_model, doctor_model, medicalrecord_model, patient_model
from app.core.database import get_db
from app.core import security

router = APIRouter(prefix="/prescription", tags=["Medical Prescription"])


# ---------------------------------------------------------------------------
# POST /prescription/{medical_record_id}  — doctor creates a prescription
# ---------------------------------------------------------------------------
@router.post(
    "/{medical_record_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=prescription_schema.DoctorPrescriptionResponse,
)
def CreateMedicalPrescription(
    medical_record_id: int,
    prescription: prescription_schema.CreatePrescription,
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

    # FIX: was MedicalRecord.record_id — correct PK column is medical_record_id
    medical_record = (
        db.query(medicalrecord_model.MedicalRecord)
        .filter(
            medicalrecord_model.MedicalRecord.medical_record_id == medical_record_id
        )
        .first()
    )
    if medical_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Medical record not found"
        )

    if medical_record.doctor_id != doctor_profile.doctor_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    existing = (
        db.query(prescription_model.Prescription)
        .filter(
            prescription_model.Prescription.medical_record_id
            == medical_record.medical_record_id
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Prescription already created"
        )

    # FIX: was medical_record.record_id — correct attribute is medical_record_id
    new_prescription = prescription_model.Prescription(
        medical_record_id=medical_record.medical_record_id,
        doctor_id=medical_record.doctor_id,
        patient_id=medical_record.patient_id,
        medicine_name=prescription.medicine_name,
        dosage=prescription.dosage,
        frequency=prescription.frequency,
        duration=prescription.duration,
        instructions=prescription.instructions,
    )

    db.add(new_prescription)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Prescription already exists for this medical record",
        ) from exc
    db.refresh(new_prescription)

    return new_prescription


# ---------------------------------------------------------------------------
# GET /prescription/doctor  — all prescriptions written by the logged-in doctor
# ---------------------------------------------------------------------------
@router.get(
    "/doctor",
    response_model=list[prescription_schema.DoctorPrescriptionResponse],
)
def ViewPrescriptionByDoctor(
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
        db.query(prescription_model.Prescription)
        .filter(
            prescription_model.Prescription.doctor_id == doctor_profile.doctor_id
        )
        .all()
    )


# ---------------------------------------------------------------------------
# GET /prescription/patient  — all prescriptions for the logged-in patient
# ---------------------------------------------------------------------------
@router.get(
    "/patient",
    status_code=status.HTTP_200_OK,
    response_model=list[prescription_schema.PatientPrescriptionResponse],
)
def ViewPrescriptionByPatient(
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    return (
        db.query(prescription_model.Prescription)
        .filter(
            prescription_model.Prescription.patient_id == patient_profile.patient_id
        )
        .all()
    )


# ---------------------------------------------------------------------------
# GET /prescription/patient/{prescription_id}  — single prescription for patient
# ---------------------------------------------------------------------------
@router.get(
    "/patient/{prescription_id}",
    status_code=status.HTTP_200_OK,
    response_model=prescription_schema.PatientPrescriptionResponse,
)
def ViewPrescriptionById(
    prescription_id: int,
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    prescription = (
        db.query(prescription_model.Prescription)
        .filter(
            prescription_model.Prescription.prescription_id == prescription_id
        )
        .first()
    )
    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prescription not found"
        )

    if prescription.patient_id != patient_profile.patient_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    return prescription


# ---------------------------------------------------------------------------
# PATCH /prescription/doctor/{prescription_id}  — doctor updates a prescription
# ---------------------------------------------------------------------------
@router.patch(
    "/doctor/{prescription_id}",
    response_model=prescription_schema.DoctorPrescriptionResponse,
)
def UpdatePrescription(
    prescription_id: int,
    update: prescription_schema.updatePrescription,
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

    prescription = (
        db.query(prescription_model.Prescription)
        .filter(prescription_model.Prescription.prescription_id == prescription_id)
        .first()
    )
    if prescription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prescription not found"
        )

    if prescription.doctor_id != doctor_profile.doctor_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    update_dict = update.model_dump(exclude_unset=True)
    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update",
        )

    for key, value in update_dict.items():
        setattr(prescription, key, value)

    db.commit()
    db.refresh(prescription)

    return prescription
