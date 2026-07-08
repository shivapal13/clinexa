from fastapi import FastAPI,APIRouter,HTTPException,status,Depends,Response
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import patient_model
from app.schemas import patient_schema
from app.core import security


router=APIRouter(
    prefix="/patient/profile",
    tags=['PatientProfile']
)


@router.post("/",status_code=status.HTTP_201_CREATED)
def CreatePatientProfile(patient_data:patient_schema.PatientProfileCreate,db:Session=Depends(get_db),current_user=Depends(security.get_current_user)):

    if(current_user.role!='Patient'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="not allowed")
    
    existing_profile=db.query(patient_model.Patient).filter(patient_model.Patient.user_id==current_user.id).first()

    if existing_profile is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="profile already existed")
    
    new_patient=patient_model.Patient(
        user_id=current_user.id,
        age=patient_data.age,
        gender=patient_data.gender,
        phone_number=patient_data.phone_number,
        blood_group=patient_data.blood_group,
        address=patient_data.address
    )

    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)

    return new_patient

@router.get("/",status_code=status.HTTP_200_OK)
def GetPatientProfile(db:Session=Depends(get_db),current_user=Depends(security.get_current_user)):

    if(current_user.role!='patient'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="not allowed")
    
    patient_data=db.query(patient_model.Patient).filter(patient_model.Patient.user_id==current_user.id).first()

    if patient_data is None:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT,detail="profile do not exist !")
    
    return patient_data


@router.patch("/",status_code=status.HTTP_200_OK)
def UpdatePatientProfile(Update_data:patient_schema.PatientProfileUpdate,
                         db:Session=Depends(get_db),
                         current_user=Depends(security.get_current_user)):
    
    if(current_user.role!='patient'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="not allowed")
    
    patient=db.query(patient_model.Patient).filter(patient_model.Patient.user_id==current_user.id)
    patient_query=patient.first()

    if patient_query is None:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT,detail="profile not found")
    
    update_data=Update_data.model_dump(exclude_unset=True)

    for key,value in update_data.items():
        setattr(patient_query,key,value)

    db.commit()
    db.refresh(patient_query) 

    return patient_query  


@router.delete("/")
def DeletePatientProfile(db:Session=Depends(get_db),current_user=Depends(security.get_current_user)):

    if(current_user.role!='patient'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="not allowed")
    
    patient_data=db.query(patient_model.Patient).filter(patient_model.Patient.user_id==current_user.id).first()

    if patient_data is None:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT,detail="profile not found")
    
    db.delete(patient_data)
    db.commit()

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )


