from fastapi import FastAPI,HTTPException,status,Depends,APIRouter
from app.schemas import prescription_schema
from app.models import prescription_model,doctor_model,medicalrecord_model,patient_model
from app.core.database import get_db
from sqlalchemy.orm import Session
from app.core import security


router=APIRouter(
    prefix="/prescription",
    tags=['Medical Prescription']
)

@router.post("/{record_id}",status_code=status.HTTP_201_CREATED)
def CreateMedicalPrescription(record_id:int,
                              prescription:prescription_schema.CreatePrescription,
                              db:Session=Depends(get_db),
                              current_user=Depends (security.get_current_user)):

    if(current_user.role!='doctor'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed")
    
    doctor_profiles=db.query(doctor_model.Doctor).filter(doctor_model.Doctor.user_id==current_user.id).first()

    if doctor_profiles is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Doctor not found")
    
    medical_record=db.query(medicalrecord_model.MedicalRecord).filter(medicalrecord_model.MedicalRecord.record_id==record_id).first()

    if medical_record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Medical record not found")
    
    if medical_record.doctor_id!=doctor_profiles.doctor_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed")
    
    existing_prescription=db.query(prescription_model.Prescription).filter(prescription_model.Prescription.medical_record_id==record_id).first()

    if existing_prescription is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="Prescription already created")
    
    new_prescription=prescription_model.Prescription(
        medical_record_id=medical_record.record_id,
        doctor_id=medical_record.doctor_id,
        patient_id=medical_record.patient_id,
        medicine_name=prescription.medicine_name,
        dosage=prescription.dosage,
        frequency=prescription.frequency,
        duration=prescription.duration,
        instructions=prescription.instructions
    )
    
    db.add(new_prescription)
    db.commit()
    db.refresh(new_prescription)

    return new_prescription

@router.get("/patient",status_code=status.HTTP_200_OK)
def ViewMedicalPrescription(db:Session=Depends(get_db),current_user=Depends(security.get_current_user)):

    if(current_user.role!='patient'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed")
    
    patient_profile=db.query(patient_model.Patient).filter(patient_model.Patient.user_id==current_user.id).first()

    if patient_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Patient not found")
    
    prescription=db.query(prescription_model.Prescription).filter(
                          prescription_model.Prescription.patient_id==patient_profile.patient_id).all()
    
    return prescription

@router.get("/patient/{prescription_id}",status_code=status.HTTP_200_OK)
def ViewPrescriptionById(prescription_id:int,db:Session=Depends(get_db),current_user=Depends(security.get_current_user)):

    if(current_user.role!='patient'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed")
    
    patient_profile=db.query(patient_model.Patient).filter(patient_model.Patient.user_id==current_user.id).first()

    if patient_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Patient not found")
    
    prescription=db.query(prescription_model.Prescription).filter(
                          prescription_model.Prescription.prescription_id==prescription_id).first()
    
    if not prescription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Prescription not found")
    
    if prescription.patient_id!=patient_profile.patient_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed")
    
    return prescription
    
@router.patch("/doctor/{prescription_id}")
def UpdatePrescription(prescription_id:int,
                       Update_prescription:prescription_schema.updatePrescription,
                       db:Session=Depends(get_db),
                       current_user=Depends(security.get_current_user)):

    if(current_user.role!='doctor'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed")

    doctor_profile=db.query(doctor_model.Doctor).filter(doctor_model.Doctor.user_id==current_user.id).first()

    if doctor_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Doctor not found")

    prescription=db.query(prescription_model.Prescription).filter(
                          prescription_model.Prescription.prescription_id==prescription_id).first()

    if prescription is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Prescription not found")

    if prescription.doctor_id!=doctor_profile.doctor_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed")

    update_dict=Update_prescription.model_dump(exclude_unset=True)  
    for key,value in update_dict.items():
        setattr(prescription,key,value)

    db.commit()
    db.refresh(prescription)

    return prescription      

    

    
