from fastapi import FastAPI,HTTPException,status,Depends,APIRouter
from app.models import medicalrecord_model,doctor_model,patient_model,appointment_model
from app.schemas import medicalrecord_schema
from app.core.database import get_db
from app.core import security
from sqlalchemy.orm import Session


router=APIRouter(
    prefix="/medicalreport",
    tags=["Medical Reports"]
)

@router.post("/{appointment_id}",status_code=status.HTTP_201_CREATED)
def CreateReport(appointment_id:int,medical_report:medicalrecord_schema.CreateMedicalRecord,
                 db:Session=Depends(get_db),current_user=Depends(security.get_current_user)):
    
    if(current_user.role!='doctor'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="not allowed")
    
    doctor_profile=db.query(doctor_model.Doctor).filter(doctor_model.Doctor.user_id==current_user.id).first()

    if doctor_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No doctor exist")
    
    appointment=db.query(appointment_model.Appointment).filter(
                        appointment_model.Appointment.appointment_id==appointment_id).first()
    
    if appointment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Appointment Not found")
    
    if appointment.doctor_id!=doctor_profile.doctor_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="not allowed")
    
    if appointment.status!="COMPLETED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Medical report can only be created for completed appointments")
    
    existing_report = db.query(
        medicalrecord_model.MedicalRecord
    ).filter(
        medicalrecord_model.MedicalRecord.appointment_id == appointment_id
    ).first()

    if existing_report:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Medical report already exists"
        )        
    new_report=medicalrecord_model.MedicalRecord(
        appointment_id=appointment.appointment_id,
        patient_id=appointment.patient_id,
        doctor_id=appointment.doctor_id,
        diagnosis=medical_report.diagnosis,
        symptoms=medical_report.symptoms,
        doctor_notes=medical_report.doctor_notes,
        follow_up_dates=medical_report.follow_up_dates
    )

    db.add(new_report)
    db.commit()
    db.refresh(new_report)

    return new_report

@router.patch("/doctor/{record_id}")
def UpdateMedicalReport(record_id:int,updateMedical_data:medicalrecord_schema.UpdateMedicalRecord,
                        db:Session=Depends(get_db),current_user=Depends(security.get_current_user)):

    if(current_user.role!='doctor'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="not allowed")
    
    doctor_profiles=db.query(doctor_model.Doctor).filter(doctor_model.Doctor.user_id==current_user.id).first()

    if doctor_profiles is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Doctor not found")
    
    medical_record=db.query(medicalrecord_model.MedicalRecord).filter(medicalrecord_model.MedicalRecord.record_id==record_id).first()

    if medical_record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Medical record do not exist")
    
    if medical_record.doctor_id!=doctor_profiles.doctor_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="not allowed")
    
    update_dict=updateMedical_data.model_dump(exclude_unset=True)

    if not update_dict:
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="No field provided for updates") 
    
    for key,value in update_dict.items():
        setattr(medical_record,key,value)   

    db.commit()
    db.refresh(medical_record)

    return medical_record    


@router.get("/patient")
def ViewPatientRecord(db:Session=Depends(get_db),current_user=Depends(security.get_current_user)):

    if(current_user.role!='patient'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="not allowed")
    
    patient_profile=db.query(patient_model.Patient).filter(patient_model.Patient.user_id==current_user.id).first()

    if patient_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="patient does not exist")
    
    medical_record=db.query(medicalrecord_model.MedicalRecord).filter(
                            medicalrecord_model.MedicalRecord.patient_id==patient_profile.patient_id).all()
    
    if not  medical_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Medical record not found")
    

    return medical_record

@router.get("/patient/{record_id}")
def ViewPatientRecord(record_id:int,db:Session=Depends(get_db),current_user=Depends(security.get_current_user)):

    if(current_user.role!='patient'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="not allowed")
    
    patient_profile=db.query(patient_model.Patient).filter(patient_model.Patient.user_id==current_user.id).first()

    if patient_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="patient does not exist")
    

    
    medical_report=db.query(medicalrecord_model.MedicalRecord).filter(
                            medicalrecord_model.MedicalRecord.record_id==record_id).first()
    
    if medical_report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Medical record not found")
    
    if medical_report.patient_id!=patient_profile.patient_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="not allowed")
    
    return medical_report


