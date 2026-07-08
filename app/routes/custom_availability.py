from fastapi import FastAPI,HTTPException,status,APIRouter,Depends
from app.core.database import Base,get_db
from app.models import custom_availability_model,doctor_model
from app.schemas import custom_availability_schema
from sqlalchemy.orm import Session
from app.core import security

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

    if current_user.role != "doctor":
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
        custom_availability_model.CustomAvailability.doctor_id == doctor_profile.id,
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
        doctor_id=doctor_profile.id,
        date=override_data.date,
        start_time=override_data.start_time,
        end_time=override_data.end_time,
        slot_duration=override_data.slot_duration,
        is_available=override_data.is_available
    )

    db.add(new_override)
    db.commit()
    db.refresh(new_override)

    return new_override


@router.get("/")
def GetCustomAvailabilities(
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user)
):

    if current_user.role != "doctor":
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

    custom_availabilities = db.query(
        custom_availability_model.CustomAvailability
    ).filter(
        custom_availability_model.CustomAvailability.doctor_id == doctor_profile.id
    ).all()

    return custom_availabilities

@router.patch("/{id}")
def UpdateCustomAvailability(
    id: int,
    custom_data: custom_availability_schema.CreateCustomAvailability,
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user)
):

    if current_user.role != "doctor":
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
    existing_custom = db.query(
        custom_availability_model.CustomAvailability
    ).filter(
        custom_availability_model.CustomAvailability.doctor_id == doctor_profile.id,
        custom_availability_model.CustomAvailability.date == custom_data.date,
        custom_availability_model.CustomAvailability.id != id
    ).first()

    if existing_custom:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Custom availability already exists for this date"
        )

    if custom_availability.doctor_id != doctor_profile.id:
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
    db.refresh(custom_availability)

    return custom_availability

@router.delete("/{id}", status_code=status.HTTP_200_OK)
def DeleteCustomAvailability(
    id: int,
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user)
):

    if current_user.role != "doctor":
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

    if custom_availability.doctor_id != doctor_profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed"
        )

    db.delete(custom_availability)
    db.commit()

    return {
        "message": "Custom availability deleted successfully"
    }


