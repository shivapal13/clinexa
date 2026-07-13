from fastapi import FastAPI,HTTPException,status,Depends,APIRouter,Response
from app.core.database import get_db
from app.models import recurring_availability_model,doctor_model
from app.schemas import recurring_availability_schema
from sqlalchemy.orm import Session
from app.core import security
from app.services import redis_service

router=APIRouter(
    prefix="/doctor/availability",
    tags=['Recurrring Availability']
)

@router.post("/",status_code=status.HTTP_201_CREATED,response_model=recurring_availability_schema.RecurringAvailabilityResponse)
def Create_recurring_avalilability(recurring_data:recurring_availability_schema.RecurringAvailabilityCreate,
                         db:Session=Depends(get_db),
                        current_user=Depends(security.get_current_user)):

       if(current_user.role!='Doctor'):
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed") 

       doctor_profile=db.query(doctor_model.Doctor).filter(doctor_model.Doctor.user_id==current_user.id).first()

       if doctor_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Doctor Profile not found")

       if recurring_data.start_time>=recurring_data.end_time:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Start time must be before end time")

       if recurring_data.slot_duration<=0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Slot duration must be greater than zero")  

        
       existing_slots=db.query(recurring_availability_model.RecurringAvailability).filter(
                                recurring_availability_model.RecurringAvailability.doctor_id==doctor_profile.doctor_id,
                                recurring_availability_model.RecurringAvailability.day_of_week==recurring_data.day_of_week).all()   


       for slot in existing_slots:
          overlap=(
                    recurring_data.start_time<slot.end_time and
                    recurring_data.end_time>slot.start_time    
                )  

          if overlap:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                    detail="slot is overlapping with  the existing slot")                   

       new_availability=recurring_availability_model.RecurringAvailability(
            
            doctor_id=doctor_profile.doctor_id,
            day_of_week=recurring_data.day_of_week,
            start_time=recurring_data.start_time,
            end_time=recurring_data.end_time,
            slot_duration=recurring_data.slot_duration
       )   

       db.add(new_availability)
       db.commit()
       redis_service.delete_key(
           f"recurring:doctor:{doctor_profile.doctor_id}"
       )
       db.refresh(new_availability)

       return new_availability


@router.get("/",response_model=list[recurring_availability_schema.RecurringAvailabilityResponse])
def GetRecurringAvailability(
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user)

):

    if current_user.role != "Doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed"
        )

    doctor_profile = db.query(
        doctor_model.Doctor
    ).filter(
        doctor_model.Doctor.user_id == current_user.id
    ).first()

    if doctor_profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor Profile not found")

    cache_key=f"recurring:doctor:{doctor_profile.doctor_id}"
    cache_availability=redis_service.get_json(cache_key)

    if cache_availability:
        return cache_availability

    availabilities = db.query(
        recurring_availability_model.RecurringAvailability
    ).filter(
        recurring_availability_model.RecurringAvailability.doctor_id == doctor_profile.doctor_id
    ).all()

    availability_reponse=[recurring_availability_schema.RecurringAvailabilityResponse.model_validate(item).model_dump() for item in availabilities]

    redis_service.set_json(
        cache_key,
        availability_reponse,
        ttl=300
    )

    return availability_reponse

@router.patch("/{id}",response_model=recurring_availability_schema.RecurringAvailabilityResponse)
def UpdateRecurringAvailability(
    id: int,
    recurring_data: recurring_availability_schema.RecurringAvailabilityUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user)
):

    if current_user.role != "Doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed"
        )

    doctor_profile = db.query(
        doctor_model.Doctor
    ).filter(
        doctor_model.Doctor.user_id == current_user.id
    ).first()

    if doctor_profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found"
        )

    availability = db.query(
        recurring_availability_model.RecurringAvailability
    ).filter(
        recurring_availability_model.RecurringAvailability.id == id
    ).first()

    if availability is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Availability not found"
        )

    if availability.doctor_id != doctor_profile.doctor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed"
        )

    if recurring_data.start_time >= recurring_data.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start time must be before end time"
        )

    if recurring_data.slot_duration is not None and recurring_data.slot_duration<=0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slot duration must be greater than zero"
        )

    existing_slots = db.query(
        recurring_availability_model.RecurringAvailability
    ).filter(
        recurring_availability_model.RecurringAvailability.doctor_id == doctor_profile.doctor_id,
        recurring_availability_model.RecurringAvailability.day_of_week == recurring_data.day_of_week,
        recurring_availability_model.RecurringAvailability.id != id
    ).all()

    for slot in existing_slots:

        overlap = (
            recurring_data.start_time < slot.end_time
            and
            recurring_data.end_time > slot.start_time
        )

        if overlap:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Availability overlaps with existing schedule"
            )

    update_data=recurring_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
     setattr(availability, key, value)

    db.commit()
    redis_service.delete_key(
        f"recurring:doctor:{doctor_profile.doctor_id}"
    )
    redis_service.delete_key(
        f"availability:doctor:{doctor_profile.doctor_id}:*"
    )
    db.refresh(availability)

    return availability

@router.delete("/{id}", status_code=status.HTTP_200_OK)
def DeleteRecurringAvailability(
    id: int,
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user)
):

    if current_user.role != "Doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed"
        )

    doctor_profile = db.query(
        doctor_model.Doctor
    ).filter(
        doctor_model.Doctor.user_id == current_user.id
    ).first()

    if doctor_profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found"
        )

    availability = db.query(
        recurring_availability_model.RecurringAvailability
    ).filter(
        recurring_availability_model.RecurringAvailability.id == id
    ).first()

    if availability is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Availability not found"
        )

    if availability.doctor_id != doctor_profile.doctor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to delete this availability"
        )

    db.delete(availability)
    db.commit()
    redis_service.delete_key(
        f"recurring:doctor:{doctor_profile.doctor_id}"
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )


