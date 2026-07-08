from fastapi import FastAPI,HTTPException,status,Depends,APIRouter
from sqlalchemy.orm import Session
from app.core.database import get_db
from datetime import date
from app.core import security
from app.services.slot_generation import get_available_slots
from app.models import doctor_model

router=APIRouter(
    prefix="/doctors",
    tags=["Doctor Discovery"]
)

@router.get("/{doctor_id}/available-slots")
def GetAvailableSlots(doctor_id:int,target_date:date,db:Session=Depends(get_db)):
    
    doctor=db.query(doctor_model.Doctor).filter(doctor_model.Doctor.doctor_id==doctor_id).first()
    

    if doctor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Doctor not found")
    
    slots=get_available_slots(
        doctor_id=doctor_id,
        target_date=target_date,
        db=db
    )
   

    return{
        "doctor_id":doctor_id,
        "date":target_date,
        "available_slots":slots
    }
    

    
