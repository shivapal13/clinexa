from fastapi import FastAPI,HTTPException,status,Depends,APIRouter,Query
from app.core.database import get_db
from app.models import appointment_model,patient_model,doctor_model,user
from app.schemas import appointment_schema
from sqlalchemy.orm import Session
from app.core import security
from datetime import date,datetime
import math
from app.core.enums import AppointmentStatus
from app.services.availability_service import resolve_availability
from app.services.slot_generation import get_available_slots
from app.tasks.email_tasks import send_confirmation_email
router=APIRouter(
    prefix="/appointments",
    tags=["Appointments"]
)


@router.post("/",status_code=status.HTTP_201_CREATED)
def CreateAppointments(appointment_data:appointment_schema.AppointmentCreate,db:Session=Depends(get_db),current_user=Depends(security.get_current_user)):

    if(current_user.role!="Patient"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed")
    
    patient_profile=db.query(patient_model.Patient).filter(patient_model.Patient.user_id==current_user.id).first()

    if patient_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Patient not found")


    doctor_profile=db.query(doctor_model.Doctor).filter(doctor_model.Doctor.doctor_id==appointment_data.doctor_id).first()

    if doctor_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Doctor not found")
    
    doctor_user = db.query(user.User).filter(
    user.User.id == doctor_profile.user_id
).first()
    
    if appointment_data.appointment_date<date.today():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Cannot book appointment for past date")
    
    if appointment_data.appointment_date==date.today() and appointment_data.appointment_time<=datetime.now().time():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Cannot book appointment for past date")
    
    slots = get_available_slots(
    doctor_id=appointment_data.doctor_id,
    target_date=appointment_data.appointment_date,
    db=db
)
    if not slots:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Doctor is not available on Date: {appointment_data.appointment_date}")

    valid_slots=[
        slot["start_time"]
        for slot in slots
    ]
    
    requested_time=appointment_data.appointment_time.strftime("%H:%M")

    if requested_time not in valid_slots:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Invalid time slot")
    
    new_appointment=appointment_model.Appointment(
        patient_id=patient_profile.patient_id,
        doctor_id=appointment_data.doctor_id,
        medical_service=appointment_data.medical_service,
        reason=appointment_data.reason,
        appointment_date=appointment_data.appointment_date,
        appointment_time=appointment_data.appointment_time,
        status=AppointmentStatus.PENDING.value
    )

    db.add(new_appointment)
    db.commit()
    db.refresh(new_appointment)
    send_confirmation_email.delay(
    email=current_user.email,
    patient_name=current_user.name,
    doctor_name=doctor_user.name,
    specialisation=doctor_profile.specialisation,
    medical_service=appointment_data.medical_service,
    appointment_date=str(appointment_data.appointment_date),
    appointment_time=str(appointment_data.appointment_time),
)
    return new_appointment

@router.get("/patient",status_code=status.HTTP_200_OK,response_model=appointment_schema.PatientAppointmentListResponse)
def GetPatientAppointments(db:Session=Depends(get_db),current_user=Depends(security.get_current_user),page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),view:str|None=None):

    if(current_user.role!='Patient'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed")
    
    patient_profile=db.query(patient_model.Patient).filter(patient_model.Patient.user_id==current_user.id).first()
    
    if patient_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Patient not found")
    query=db.query(appointment_model.Appointment).filter(appointment_model.Appointment.patient_id==patient_profile.patient_id)
    today=date.today()

    if view:
        view=view.upper()
    
    if view and view not in ["UPCOMING", "HISTORY"]:
     raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="view must be UPCOMING or HISTORY"
    )

    if view=="UPCOMING":
        query=query.filter(appointment_model.Appointment.appointment_date>=today
    )
        
    elif view=="HISTORY":
      query=query.filter(appointment_model.Appointment.appointment_date<today
    )

    total=query.count()
    offset=(page-1)*page_size
    
    patient_appointments = (
     query
    .order_by(
        appointment_model.Appointment.appointment_date,
        appointment_model.Appointment.appointment_time
    )
    .offset(offset)
    .limit(page_size)
    .all()
)

    total_pages=math.ceil(total/page_size) if total > 0 else 0

    return {
    "total": total,
    "page": page,
    "page_size": page_size,
    "total_pages": total_pages,
    "appointments": patient_appointments
    }

@router.get("/patient/{appointment_id}",status_code=status.HTTP_200_OK,response_model=appointment_schema.PatientAppointmentsResponse)
def GetPatientAppointmentById(appointment_id:int,db:Session=Depends(get_db),current_user=Depends(security.get_current_user)):

    if(current_user.role!='Patient'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed")
    
    patient_profile=db.query(patient_model.Patient).filter(patient_model.Patient.user_id==current_user.id).first()
    
    if patient_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Patient not found")
    
    patient_appointments=db.query(appointment_model.Appointment).filter(appointment_model.Appointment.patient_id==patient_profile.patient_id,
                                                                        appointment_model.Appointment.appointment_id==appointment_id).first()
    
    if patient_appointments is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Appointment not found")
    
    return patient_appointments

    
@router.patch("/{appointment_id}")
def UpdateAppointment(appointment_id:int,
                      update_appointment:appointment_schema.AppointmentUpdate,
                            db:Session=Depends(get_db),
                            current_user=Depends(security.get_current_user)):

    if(current_user.role!='Patient'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed")
    
    patient_profile=db.query(patient_model.Patient).filter(patient_model.Patient.user_id==current_user.id).first()

    if patient_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Patient not found")
    
    appointment=db.query(appointment_model.Appointment).filter(appointment_model.Appointment.appointment_id==appointment_id).first()

    if appointment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Appointment not found")
    
    if appointment.patient_id!=patient_profile.patient_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not Allowed")

    if appointment.status in (
        AppointmentStatus.CANCELLED.value,
        AppointmentStatus.COMPLETED.value,
        ):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Cannot update this appointment")
    
    update_data=update_appointment.model_dump(exclude_unset=True)

    appointment_date=update_data.get(
        "appointment_date",
        appointment.appointment_date
    )

    appointment_time=update_data.get(
        "appointment_time",
        appointment.appointment_time
    )

    if appointment_date<date.today():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Cannot update past appointments")
    
    if appointment_date==date.today() and appointment_time<=datetime.now().time():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Cannot update past appointment")

    slots = get_available_slots(
    doctor_id=appointment.doctor_id,
    target_date=appointment_date,
    db=db,
    exclude_appointment_id=appointment_id
)   
    
    if not slots:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"No slot are available for Date: {appointment_date}"
    )

    valid_slots=[
        slot["start_time"]
        for slot in slots
    ]

    requested_time=appointment_time.strftime("%H:%M")

    if requested_time not in valid_slots:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Invalid time Slot")
    
    for key,value in update_data.items():
        setattr(appointment,key,value)

    db.commit()
    db.refresh(appointment)

    return {"message":"Appointment Updated Successfully",
            "Appointment_details":appointment}

@router.get(
    "/doctor",
    status_code=status.HTTP_200_OK,
    response_model=appointment_schema.DoctorAppointmentListResponse
)
def GetDoctorAppointments(
    status: AppointmentStatus | None = None,
    appointment_date: date | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user)
):

    if current_user.role != "Doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed"
        )

    doctor_profile = db.query(doctor_model.Doctor).filter(
        doctor_model.Doctor.user_id == current_user.id
    ).first()

    if doctor_profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found"
        )

    query = db.query(appointment_model.Appointment).filter(
        appointment_model.Appointment.doctor_id == doctor_profile.doctor_id
    )

    if status:
        query = query.filter(
            appointment_model.Appointment.status ==status.value
        )

    if appointment_date:
        query = query.filter(
            appointment_model.Appointment.appointment_date == appointment_date
        )

    total = query.count()

    offset = (page - 1) * page_size

    appointments = (
        query
        .order_by(
            appointment_model.Appointment.appointment_date,
            appointment_model.Appointment.appointment_time
        )
        .offset(offset)
        .limit(page_size)
        .all()
    )

    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "appointments": appointments
    }

@router.patch("/{appointment_id}/cancel")
def CancelDoctorAppointment(appointment_id:int,
                            db:Session=Depends(get_db),
                            current_user=Depends(security.get_current_user)):

    if(current_user.role!='Doctor'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed")
    
    doctor_profile=db.query(doctor_model.Doctor).filter(doctor_model.Doctor.user_id==current_user.id).first()

    if doctor_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Doctor not found")
    
    appointment=db.query(appointment_model.Appointment).filter(appointment_model.Appointment.appointment_id==appointment_id).first()

    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No appointments Found")
    
    if(appointment.doctor_id!=doctor_profile.doctor_id):

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not allowed")

    if appointment.status in [AppointmentStatus.CANCELLED.value,AppointmentStatus.COMPLETED.value]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Cannot cancel this appointment")
    
    if (
    appointment.appointment_date < date.today()
    or (
        appointment.appointment_date == date.today()
        and appointment.appointment_time <= datetime.now().time()
    )
):
     raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Cannot cancel a past appointment"
    )

    appointment.status =AppointmentStatus.CANCELLED.value

    db.commit()
    db.refresh(appointment)

    return {
    "message": "Appointment cancelled successfully",
    "Cancelled_by":doctor_profile.doctor_id,
    "appointment": appointment
}


