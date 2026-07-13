from fastapi import HTTPException,status,APIRouter,Depends,Response
from app.core.database import get_db
from app.models import custom_availability_model,doctor_model
from app.schemas import custom_availability_schema
from sqlalchemy.orm import Session
from app.core import security
from app.services import redis_service
router=APIRouter(
    prefix="/doctor/availability/override",
    tags=['CustomAvailability']
)

@router.post("/", status_code=status.HTTP_201_CREATED)
def CreateOverrideAvailability(
    override_data: custom_availability_schema.CreateCustomAvailability,
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


    existing_override = db.query(
        custom_availability_model.CustomAvailability
    ).filter(
        custom_availability_model.CustomAvailability.doctor_id == doctor_profile.doctor_id,
        custom_availability_model.CustomAvailability.date == override_data.date
    ).first()

    if existing_override:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Override already exists for this date"
        )

    if override_data.is_available:

        if (
            override_data.start_time is None
            or override_data.end_time is None
            or override_data.slot_duration is None
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start time, end time and slot duration are required"
            )

        if override_data.start_time >= override_data.end_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start time must be before end time"
            )

        if override_data.slot_duration <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Slot duration must be greater than zero"
            )

    new_override = custom_availability_model.CustomAvailability(
        doctor_id=doctor_profile.doctor_id,
        date=override_data.date,
        start_time=override_data.start_time,
        end_time=override_data.end_time,
        slot_duration=override_data.slot_duration,
        is_available=override_data.is_available
    )

    db.add(new_override)
    db.commit()
    redis_service.delete_key(
        f"custom:doctor:{doctor_profile.doctor_id}:{new_override.date}"
    )
    db.refresh(new_override)

    return new_override


@router.get("/",response_model=list[custom_availability_schema.CustomAvailabilityResponse])
def GetCustomAvailabilities(
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

    cache_key=f"custom:doctor:{doctor_profile.doctor_id}"

    cache_availability=redis_service.get_json(cache_key)

    if cache_availability:
        return cache_availability

    custom_availabilities = db.query(
        custom_availability_model.CustomAvailability
    ).filter(
        custom_availability_model.CustomAvailability.doctor_id == doctor_profile.doctor_id
    ).all()

    custom_response=[custom_availability_schema.CustomAvailabilityResponse.model_validate(item).model_dump() for item in custom_availabilities]

    redis_service.set_json(
        cache_key,
        custom_response,
        ttl=300
    )

    return custom_response

@router.patch("/{id}",response_model=custom_availability_schema.CustomAvailabilityResponse)
def UpdateCustomAvailability(
    id: int,
    custom_data: custom_availability_schema.CreateCustomAvailability,
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
            detail="Not found"
        )

    custom_availability = db.query(
        custom_availability_model.CustomAvailability
    ).filter(
        custom_availability_model.CustomAvailability.id == id
    ).first()

    if custom_availability is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Custom availability not found"
        )
    old_date=custom_availability.date
    existing_custom = db.query(
        custom_availability_model.CustomAvailability
    ).filter(
        custom_availability_model.CustomAvailability.doctor_id == doctor_profile.doctor_id,
        custom_availability_model.CustomAvailability.date == custom_data.date,
        custom_availability_model.CustomAvailability.id != id
    ).first()

    if existing_custom:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Custom availability already exists for this date"
        )

    if custom_availability.doctor_id != doctor_profile.doctor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed"
        )

    if custom_data.is_available:

        if (
            custom_data.start_time is None or
            custom_data.end_time is None or
            custom_data.slot_duration is None
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start time, end time and slot duration are required"
            )

        if custom_data.start_time >= custom_data.end_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start time must be before end time"
            )

        if custom_data.slot_duration <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Slot duration must be greater than zero"
            )

    custom_availability.date = custom_data.date
    custom_availability.start_time = custom_data.start_time
    custom_availability.end_time = custom_data.end_time
    custom_availability.slot_duration = custom_data.slot_duration
    custom_availability.is_available = custom_data.is_available

    db.commit()
    redis_service.delete_key(
        f"custom:doctor:{doctor_profile.doctor_id}:{custom_availability.date}"
    )
    redis_service.delete_key(
        f"availability:doctor:{doctor_profile.doctor_id}:{old_date}"
    )
    redis_service.delete_key(
        f"availability:doctor:{doctor_profile.doctor_id}:{custom_data.date}"
    )
    db.refresh(custom_availability)

    return custom_availability

@router.delete("/{id}")
def DeleteCustomAvailability(
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

    custom_availability = db.query(
        custom_availability_model.CustomAvailability
    ).filter(
        custom_availability_model.CustomAvailability.id == id
    ).first()

    if custom_availability is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Custom availability not found"
        )

    if custom_availability.doctor_id != doctor_profile.doctor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed"
        )

    db.delete(custom_availability)
    db.commit()
    redis_service.delete_key(
        f"custom:doctor:{doctor_profile.doctor_id}:{custom_availability.date}"
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )


