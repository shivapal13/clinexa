from fastapi import FastAPI,HTTPException,status,Depends,APIRouter
from sqlalchemy.orm import Session
from app.core.database import get_db
from datetime import date
from app.core import security
from app.services.slot_generation import get_available_slots
from app.models import doctor_model
from app.services import redis_service
from app.schemas.recurring_availability_schema import AvailabilityResponse
router=APIRouter(
    prefix="/doctors",
    tags=["Doctor Discovery"]
)

@router.get("/{doctor_id}/available-slots",response_model=AvailabilityResponse)
def GetAvailableSlots(doctor_id:int,target_date:date,db:Session=Depends(get_db)):

    cache_key=f"availability:doctor:{doctor_id}:{target_date}"

    cache_slots=redis_service.get_json(cache_key)

    if cache_slots:
       return cache_slots
    
    doctor=db.query(doctor_model.Doctor).filter(doctor_model.Doctor.doctor_id==doctor_id).first()
    

    if doctor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Doctor not found")
    
    slots=get_available_slots( doctor_id=doctor_id, target_date=target_date, db=db )

    response={
        "doctor_id":doctor_id,
        "date":target_date,
        "available_slots":slots
    }

    slots_response=AvailabilityResponse.model_validate(response).model_dump()
   
    redis_service.set_json(
        cache_key,
        slots_response,
        ttl=120
    )
    return slots_response
    

    
