from datetime import date,time,timedelta,datetime
from sqlalchemy.orm import Session
from fastapi import FastAPI,Depends
from app.core.database import get_db
from app.services.availability_service import resolve_availability
def generate_slots(start_time:time,end_time:time,slot_duration:int):
   
    slots=[]
    
    current=datetime.combine(
        datetime.today(),
        start_time
    )
    

    end=datetime.combine(
        datetime.today(),
        end_time
    )
    

    while current+timedelta(minutes=slot_duration)<=end:
       
        slot_end=current+timedelta(minutes=slot_duration)

        slots.append({
            "start_time": current.time().strftime("%H:%M"),
             "end_time": slot_end.time().strftime("%H:%M"),
        })
        current=slot_end

    return slots

def get_available_slots(doctor_id:int,target_date:date,db:Session=Depends(get_db)):

    

    availability=resolve_availability(
        doctor_id=doctor_id,
        target_date=target_date,
        db=db
    )
    
    if availability is None:
        return []
    
  
    
    slots=generate_slots(
        availability.start_time,
        availability.end_time,
        availability.slot_duration
    )
  

    return slots

