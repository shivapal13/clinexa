from datetime import date,time,timedelta,datetime
from sqlalchemy.orm import Session
from app.services.availability_service import resolve_availability
from app.models import appointment_model
from app.core.enums import AppointmentStatus
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

def get_available_slots(doctor_id:int,target_date:date,db:Session,exclude_appointment_id:int|None=None):

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

    query=db.query(appointment_model.Appointment).filter(appointment_model.Appointment.doctor_id==doctor_id,
                                                                       appointment_model.Appointment.appointment_date==target_date,
                                                                       appointment_model.Appointment.status in [AppointmentStatus.PENDING.value,
                                                                                                                AppointmentStatus.CONFIRMED.value])
    
    if exclude_appointment_id is not None:
        query=query.filter(appointment_model.Appointment.appointment_id!=exclude_appointment_id)

    booked_appointments=query.all()
    booked_times={
        appointment.appointment_time.strftime("%H:%M")
        for appointment in booked_appointments
    }

    available_slots=[
        slot
        for slot in slots
        if slot["start_time"] not in booked_times
    ]
    return available_slots

