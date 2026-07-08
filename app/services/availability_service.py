from fastapi import Depends
from app.models import recurring_availability_model,custom_availability_model
from sqlalchemy.orm import Session
from datetime import date
from app.core.database import get_db
 

def resolve_availability(doctor_id:int,target_date:date,db:Session=Depends(get_db)):
    custom_availability=db.query(custom_availability_model.CustomAvailability).filter(custom_availability_model.CustomAvailability.doctor_id==doctor_id,
                                                                    custom_availability_model.CustomAvailability.date==target_date).first()
      
    if custom_availability:
            if not custom_availability.CustomAvailability.is_available:
                  return None
            
            return custom_availability 
    
    weekday = target_date.strftime("%A").upper()

    recurring_availability = db.query(
    recurring_availability_model.RecurringAvailability
     ).filter(
    recurring_availability_model.RecurringAvailability.doctor_id == doctor_id,
    recurring_availability_model.RecurringAvailability.day_of_week == weekday
    ).first()
    

    if recurring_availability:
     return recurring_availability

    return None

        
        
                  
            